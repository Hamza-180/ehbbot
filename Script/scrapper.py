from bs4 import BeautifulSoup
import requests
import json

# Lijst van URLs van de EHB-website die je wilt crawlen
urls = [
    'https://www.erasmushogeschool.be/nl/opleidingen',
    # Voeg andere URLs toe zoals nodig
]

data = []

for url in urls:
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Pas deze selectoren aan op basis van de structuur van de website
    programs = soup.find_all('div', class_='program')
    for program in programs:
        title = program.find('h2').text.strip()
        description = program.find('p').text.strip()
        data.append({
            'courseName': title,
            'description': description
        })

# Opslaan van de data in een JSON-bestand
with open('ehb_data.json', 'w') as f:
    json.dump(data, f)
