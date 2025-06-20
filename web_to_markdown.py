import requests
from bs4 import BeautifulSoup
import sys
import os
from urllib.parse import urlparse
import re
import html2text

def clean_html(html_content):
    """HTML etiketlerini temizler ve satır sonlarını boşlukla değiştirir."""
    if html_content is None:
        return ""
    # HTML etiketlerini kaldır
    # clean = re.compile('<.*?>') # Bu satır gereksiz, BeautifulSoup get_text() kullanacağız
    text = str(html_content) # BeautifulSoup elementini stringe çevir
    # Satır sonlarını ve fazla boşlukları temizle
    text = text.replace('\n', ' ').replace('\r', '').strip()
    text = re.sub(r'\s+', ' ', text) # Birden multiple boşluğu tek boşluğa indir
    return text

def table_to_markdown(table_element):
    """BeautifulSoup tablo elementini Markdown formatına dönüştürür."""
    markdown_table = ""
    rows = table_element.find_all('tr')

    if not rows:
        return ""

    # Başlık satırı
    headers = [cell.get_text().strip() for cell in rows[0].find_all(['th', 'td'])]
    markdown_table += "| " + " | ".join(headers) + " |\n"
    markdown_table += "| " + " | ".join(["---"] * len(headers)) + " |\n"

    # Veri satırları
    for row in rows[1:]:
        cells = [cell.get_text().strip() for cell in row.find_all(['td', 'th'])]
        markdown_table += "| " + " | ".join(cells) + " |\n"

    return markdown_table

def web_to_markdown(url):
    """
    Belirtilen URL'deki web sayfasını çeker ve Markdown formatına dönüştürür.
    Ana içeriği bulmaya çalışır, istenmeyen kısımları kaldırır ve tabloları özel olarak işler.
    """
    try:
        response = requests.get(url)
        response.raise_for_status() # HTTP hataları için istisna fırlat

        soup = BeautifulSoup(response.content, 'html.parser')

        # İstenmeyen bölümleri kaldırma
        unwanted_sections = [
            "Related posts:",
            "Categories:",
            "AWS Training",
            "AWS Certifications",
            "Find Answers",
            "Connect",
            "Get the Free Beginner's Guide to AWS Certification",
            "Follow",
            "Terms",
            "Fast-track your cloud career with our 🎯 Cloud Bootcamps" # Pop-up benzeri kısım
        ]

        for section_text in unwanted_sections:
            # Metni içeren elementleri bulmaya çalış
            elements_with_text = soup.find_all(string=lambda text: text and section_text in text)
            for element in elements_with_text:
                # Bulunan elementin üst elementlerinden birini kaldırarak tüm bölümü temizle
                # Dikkatli olmak gerekiyor, çok üst bir elementi kaldırmak sayfanın büyük bir kısmını silebilir
                # Burada örnek olarak en yakın ebeveyn div'i kaldırmayı deniyoruz
                parent_div = element.find_parent('div')
                if parent_div:
                    parent_div.decompose()
                else:
                    # Eğer div bulunamazsa, elementin kendisini kaldır
                    element.extract()


        # Ana içeriği bulmaya çalış (istenmeyen kısımlar kaldırıldıktan sonra)
        main_content = soup.find('article') or soup.find('main') or soup.find('div', id='main-content') or soup.find('div', class_='content') or soup.find('div', class_='entry-content')

        if main_content:
            content_soup = main_content
        else:
            content_soup = soup.body if soup.body else soup

        # Tabloları bul ve geçici olarak işaretle
        tables = content_soup.find_all('table')
        for i, table in enumerate(tables):
            # Tabloyu placeholder ile değiştirirken, orijinal tablo elementini sakla
            placeholder = soup.new_tag("p")
            placeholder.string = f"<!-- TABLE_PLACEHOLDER_{i} -->"
            table.replace_with(placeholder)

        # Geri kalan içeriği html2text ile dönüştür
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.bodywidth = 0 # Satır kırmayı devre dışı bırak
        h.tables = False # html2text'in tablo işlemesini kapat
        # Sadece ana içerik veya body'nin HTML'ini html2text'e ver
        markdown_content = h.handle(str(content_soup))

        # İşaretlenmiş yerlere dönüştürülmüş tabloları ekle
        for i, table in enumerate(tables):
            markdown_table = table_to_markdown(table)
            placeholder_string = f"<!-- TABLE_PLACEHOLDER_{i} -->"
            # html2text, placeholder stringini de dönüştürebilir, bu yüzden tam eşleşme arayalım
            markdown_content = markdown_content.replace(placeholder_string, markdown_table, 1)


        # Başlangıçtaki ve sondaki gereksiz boş satırları temizle
        markdown_content = markdown_content.strip()

        return markdown_content

    except requests.exceptions.RequestException as e:
        return f"Hata: Web sayfası çekilemedi - {e}"
    except Exception as e:
        # Hata ayıklama için hatayı yazdır
        import traceback
        traceback.print_exc()
        return f"Hata: Dönüştürme sırasında bir sorun oluştu - {e}"

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Kullanım: python web_to_markdown.py <URL>")
        sys.exit(1)

    url = sys.argv[1]
    markdown_output = web_to_markdown(url)

    if markdown_output.startswith("Hata:"):
        print(markdown_output)
        sys.exit(1)
    else:
        # Dosya adını URL'den türet
        parsed_url = urlparse(url)
        # Hostname'i ve path'in ilk kısmını al, geçersiz karakterleri temizle
        filename = parsed_url.netloc.replace('.', '_').replace('-', '_')
        if parsed_url.path and parsed_url.path != '/':
             # Path'in ilk kısmını al ve temizle
            path_segment = parsed_url.path.strip('/').split('/')[0]
            filename = f"{filename}_{path_segment.replace('.', '_').replace('-', '_')}"

        filename = f"{filename}.md"
        # Dosya adındaki geçersiz karakterleri temizle
        filename = re.sub(r'[^\w.-]', '_', filename)
        filename = filename.replace('__', '_') # Ardışık alt çizgileri tek alt çizgiye indir
        filename = filename.strip('_') # Başlangıç ve sondaki alt çizgileri kaldır
        if not filename.endswith(".md"):
            filename += ".md"
        if filename == ".md": # Eğer temizleme sonucunda sadece .md kalırsa varsayılan bir isim ver
             filename = "output.md"


        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(markdown_output)
            print(f"Web sayfası başarıyla '{filename}' olarak kaydedildi.")
        except Exception as e:
            print(f"Hata: Dosya yazılırken bir sorun oluştu - {e}")
            sys.exit(1)