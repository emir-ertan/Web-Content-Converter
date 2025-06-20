import requests
from bs4 import BeautifulSoup
import sys
import os
from urllib.parse import urlparse, urljoin
import re
import html2text

def clean_html(html_content):
    """HTML etiketlerini temizler ve satır sonlarını boşlukla değiştirir."""
    if html_content is None:
        return ""
    text = str(html_content)
    text = text.replace('\n', ' ').replace('\r', '').strip()
    text = re.sub(r'\s+', ' ', text)
    return text

def table_to_markdown(table_element):
    """BeautifulSoup tablo elementini Markdown formatına dönüştürür."""
    markdown_table = ""
    rows = table_element.find_all('tr')

    if not rows:
        return ""

    headers = [cell.get_text().strip() for cell in rows[0].find_all(['th', 'td'])]
    markdown_table += "| " + " | ".join(headers) + " |\n"
    markdown_table += "| " + " | ".join(["---"] * len(headers)) + " |\n"

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
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # İstenmeyen bölümleri kaldırma (web_to_markdown.py'deki aynı mantık)
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
            "Fast-track your cloud career with our 🎯 Cloud Bootcamps"
        ]

        for section_text in unwanted_sections:
            elements_with_text = soup.find_all(string=lambda text: text and section_text in text)
            for element in elements_with_text:
                try:
                    # Eğer element bir NavigableString ise, ebeveynine eriş
                    if isinstance(element, BeautifulSoup.NavigableString):
                        parent_element = element.parent
                    else:
                        parent_element = element

                    # Ebeveyn element üzerinden div'i bulmaya çalış
                    parent_div = parent_element.find_parent('div')
                    if parent_div:
                        parent_div.decompose()
                    else:
                        # Eğer div bulunamazsa, elementin kendisini kaldır
                        element.extract()
                except Exception as e:
                    # Hata oluşursa, bu elementi atla ve devam et
                    print(f"Kaldırma hatası: {e} - Element: {element}")
                    continue

        # Ana içeriği bulmaya çalış (istenmeyen kısımlar kaldırıldıktan sonra)
        main_content = soup.find('article') or soup.find('main') or soup.find('div', id='main-content') or soup.find('div', class_='content') or soup.find('div', class_='entry-content')

        if main_content:
            content_soup = main_content
        else:
            content_soup = soup.body if soup.body else soup

        # Tabloları ve görselleri bul ve geçici olarak işaretle
        tables = content_soup.find_all('table')
        images = content_soup.find_all('img')

        for i, table in enumerate(tables):
            placeholder = soup.new_tag("p")
            placeholder.string = f"<!-- TABLE_PLACEHOLDER_{i} -->"
            table.replace_with(placeholder)

        for i, img in enumerate(images):
            placeholder = soup.new_tag("p")
            placeholder.string = f"<!-- IMAGE_PLACEHOLDER_{i} -->"
            img.replace_with(placeholder)


        # Geri kalan içeriği html2text ile dönüştür
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.bodywidth = 0
        h.tables = False # html2text'in tablo işlemesini kapat
        h.ignore_images = True # html2text'in görsel işlemesini kapat
        markdown_content = h.handle(str(content_soup))

        # İşaretlenmiş yerlere dönüştürülmüş tabloları ve görselleri ekle
        for i, table in enumerate(tables):
            markdown_table = table_to_markdown(table)
            placeholder_string = f"<!-- TABLE_PLACEHOLDER_{i} -->"
            markdown_content = markdown_content.replace(placeholder_string, markdown_table, 1)

        for i, img in enumerate(images):
            alt_text = img.get('alt', '')
            img_url = img.get('src', '')
            # Mutlak URL'ye dönüştür
            if img_url:
                 img_url = urljoin(url, img_url)

            markdown_image = f"![{alt_text}]({img_url})"
            placeholder_string = f"<!-- IMAGE_PLACEHOLDER_{i} -->"
            markdown_content = markdown_content.replace(placeholder_string, markdown_image, 1)

        markdown_content = markdown_content.strip()

        # "Related posts:" başlığını ve sonrasını sil
        related_posts_index = markdown_content.find("### Related posts:")
        if related_posts_index != -1:
            markdown_content = markdown_content[:related_posts_index].strip()

        return markdown_content

    except requests.exceptions.RequestException as e:
        print(f"Hata: Web sayfası çekilemedi - {e}")
        return None
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Hata: Dönüştürme sırasında bir sorun oluştu - {e}")
        return None

def generate_filename_from_url(url):
    """URL'den temiz bir dosya adı türetir."""
    parsed_url = urlparse(url)
    filename = parsed_url.netloc.replace('.', '_').replace('-', '_')
    if parsed_url.path and parsed_url.path != '/':
        path_segment = parsed_url.path.strip('/').split('/')[0]
        filename = f"{filename}_{path_segment.replace('.', '_').replace('-', '_')}"

    filename = f"{filename}.md"
    filename = re.sub(r'[^\w.-]', '_', filename)
    filename = filename.replace('__', '_')
    filename = filename.strip('_')
    if not filename.endswith(".md"):
        filename += ".md"
    if filename == ".md":
         filename = "output.md"
    return filename

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Kullanım: python txt_link_to_md.py <linkler_dosyası>")
        sys.exit(1)

    links_filename = sys.argv[1]

    if not os.path.exists(links_filename):
        print(f"Hata: '{links_filename}' dosyası bulunamadı.")
        sys.exit(1)

    try:
        with open(links_filename, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]

        if not urls:
            print(f"'{links_filename}' dosyasında hiç link bulunamadı.")
            sys.exit(0)

        for url in urls:
            print(f"Dönüştürülüyor: {url}")
            markdown_output = web_to_markdown(url)

            if markdown_output:
                output_filename = generate_filename_from_url(url)
                try:
                    with open(output_filename, "w", encoding="utf-8") as f:
                        f.write(markdown_output)
                    print(f"Başarıyla kaydedildi: '{output_filename}'")
                except Exception as e:
                    print(f"Hata: '{output_filename}' dosyası yazılırken bir sorun oluştu - {e}")
            else:
                print(f"Uyarı: '{url}' için içerik alınamadı veya dönüştürülemedi.")

    except Exception as e:
        print(f"Hata: '{links_filename}' dosyası okunurken bir sorun oluştu - {e}")
        sys.exit(1)