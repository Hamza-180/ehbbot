import os
import json
from bs4 import BeautifulSoup

# Répertoire contenant les fichiers HTML
html_dir = "erasmus-site-parsed"

# Liste pour stocker les programmes structurés
programs = []

# Parcourir les fichiers HTML et extraire les données
for filename in os.listdir(html_dir):
    if filename.endswith('.html'):
        filepath = os.path.join(html_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')

            # Extraire les informations spécifiques du programme
            course_name_tag = soup.find('h1', class_='page-header')
            course_name = course_name_tag.text.strip() if course_name_tag else 'N/A'

            description_tag = soup.find('div', class_='field--name-field-text')
            description = description_tag.text.strip() if description_tag else 'N/A'


            career_opportunities = 'N/A'

            programs.append({
                'courseName': course_name,
                'description': description,
                'careerOpportunities': career_opportunities
            })

# Convertir en JSON et sauvegarder dans un fichier
with open('../programs.json', 'w', encoding='utf-8') as json_file:
    json.dump(programs, json_file, indent=4, ensure_ascii=False)
