import requests
from bs4 import BeautifulSoup
import sys
import os
from urllib.parse import urljoin

def get_links_from_url(url):
    """
    Belirtilen URL'deki web sayfasından tüm linkleri çeker.
    """
    try:
        response = requests.get(url)
        response.raise_for_status() # HTTP hataları için istisna fırlat

        soup = BeautifulSoup(response.content, 'html.parser')

        links = []
        # Belirtilen CSS seçiciye uyan linkleri bul
        for link in soup.select('.post-grid.bb-grid .ratio-wrap a'):
            href = link['href']
            # Mutlak URL'ye dönüştür
            full_url = urljoin(url, href)
            links.append(full_url)

        return links

    except requests.exceptions.RequestException as e:
        print(f"Hata: Web sayfası çekilemedi - {e}")
        return None
    except Exception as e:
        print(f"Hata: Linkler alınırken bir sorun oluştu - {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Kullanım: python get_links.py <URL>")
        sys.exit(1)

    url = sys.argv[1]
    all_links = get_links_from_url(url)

    if all_links is not None:
        output_filename = "linkler.txt"
        try:
            with open(output_filename, "w", encoding="utf-8") as f:
                for link in all_links:
                    f.write(link + "\n")
            print(f"Linkler başarıyla '{output_filename}' dosyasına kaydedildi.")
        except Exception as e:
            print(f"Hata: Dosya yazılırken bir sorun oluştu - {e}")
            sys.exit(1)
    else:
        sys.exit(1)