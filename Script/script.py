import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from tqdm import tqdm
import os


base_url = "https://www.erasmushogeschool.be/nl/opleidingen"


r = requests.get(base_url)
r.raise_for_status()


soup = BeautifulSoup(r.content, 'html.parser')


links = soup.findAll('a')


filtered_links = []
for link in links:
    href = link.get('href')
    if href and href.startswith('/nl/opleidingen/'):
        full_url = urljoin(base_url, href)
        if full_url not in filtered_links:
            filtered_links.append(full_url)
    elif href and href.startswith('https://www.erasmushogeschool.be/nl/') and not href.startswith('https://www.erasmushogeschool.be/nl/opleidingen') and href.count('/') == 4:
        if href not in filtered_links:
            filtered_links.append(href)


os.makedirs("erasmus-site-parsed", exist_ok=True)


for link in tqdm(filtered_links):
    try:

        r = requests.get(link)
        r.raise_for_status()

        # Utiliser 'html.parser' pour parser la page
        soup = BeautifulSoup(r.content, 'html.parser')

        # Générer le nom de fichier
        file_name = link.replace('https://www.erasmushogeschool.be/nl/', '').replace('/', '_') + '.html'

        # Écrire le contenu parsé dans un fichier
        with open(f"erasmus-site-parsed/{file_name}", "w", encoding='utf-8') as file:
            file.write(str(soup.prettify()))
        print(f"Saved {file_name}")
    except requests.RequestException as e:
        print(f"Failed to retrieve {link}: {e}")
