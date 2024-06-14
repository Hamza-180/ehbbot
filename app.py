import os
import logging
from flask import Flask, request, jsonify, render_template
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient
import openai
import json
import requests
from bs4 import BeautifulSoup
import threading

app = Flask(__name__, static_folder='static')

# Configuratie van logging
logging.basicConfig(level=logging.DEBUG)  # Set logging level to DEBUG for detailed output

# Azure Cognitive Search configuratie
search_service_name = "hamzasearch"
index_name = "programs-index"
search_key = "b0Kqp7pnOtjS3vHZprCNejAHlwSv7k0DIk1yhZItSOAzSeAOew0Q"

try:
    search_client = SearchClient(
        endpoint=f"https://{search_service_name}.search.windows.net",
        index_name=index_name,
        credential=AzureKeyCredential(search_key)
    )
    logging.info("Connected to Azure Cognitive Search successfully.")
except Exception as e:
    logging.error(f"Failed to connect to Azure Cognitive Search: {e}")

# Azure OpenAI configuratie
openai.api_type = "azure"
openai.api_base = "https://erasmusbotopenai.openai.azure.com/"
openai.api_version = "2022-12-01"
openai.api_key = "a55fd169aff44c7bb7574148f12ff8eb"

# Azure Blob Storage configuratie
connect_str = "DefaultEndpointsProtocol=https;AccountName=hamzastorag;AccountKey=3rEtDek+sP0tssRHLRjIYZARl2j3FHzKSEINZiJ7vCy9mI+wMBOZUfq3ELkVkMLWP53Fs4R1c9a8+AStHJ/euQ==;EndpointSuffix=core.windows.net"
try:
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    logging.info("Connected to Azure Blob Storage successfully.")
except Exception as e:
    logging.error(f"Failed to connect to Azure Blob Storage: {e}")

container_name = "ehbdata"

# Cache for blob data to reduce repeated access times
blob_data_cache = None

def load_html_files():
    html_data = []
    directory = 'local_html_files'
    for filename in os.listdir(directory):
        if filename.endswith('.html'):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file, 'html.parser')
                text = soup.get_text(separator=' ', strip=True)
                html_data.append({'name': filename, 'content': text})
    return html_data

def load_blob_data():
    global blob_data_cache
    if blob_data_cache is not None:
        return blob_data_cache

    try:
        container_client = blob_service_client.get_container_client(container_name)
        blobs = container_client.list_blobs()

        all_data = []
        for blob in blobs:
            blob_data = read_blob_data(blob.name)
            if not blob_data:
                continue

            if blob.name.endswith('.json'):
                try:
                    data = json.loads(blob_data)
                    all_data.extend(data)
                except json.JSONDecodeError as e:
                    logging.error(f"Error decoding JSON data for {blob.name}: {e}")
            elif blob.name.endswith('.html'):
                html_data = read_html_blob_data(blob.name)
                if html_data:
                    soup = BeautifulSoup(html_data, 'html.parser')
                    text = soup.get_text(separator=' ', strip=True)
                    all_data.append({'name': blob.name, 'content': text})
        blob_data_cache = all_data
        logging.debug("Blob data loaded successfully")
        return all_data
    except Exception as e:
        logging.error(f"Error listing blobs: {e}")
        return []

def read_blob_data(blob_name):
    try:
        blob_client = blob_service_client.get_blob_client(container_name, blob_name)
        return blob_client.download_blob().readall()
    except Exception as e:
        logging.error(f"Error reading blob data for {blob_name}: {e}")
        return None

def read_html_blob_data(blob_name):
    try:
        blob_data = read_blob_data(blob_name)
        if blob_data:
            return blob_data.decode('utf-8')
        return None
    except Exception as e:
        logging.error(f"Error reading HTML blob data for {blob_name}: {e}")
        return None

def truncate_text(text, max_length=500):
    return text[:max_length] + "..." if len(text) > max_length else text

def scrape_erasmushogeschool(query):
    try:
        base_url = "https://www.erasmushogeschool.be/nl"
        search_url = f"{base_url}/search/node/{query}"
        response = requests.get(search_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            for result in soup.select('.search-result'):
                title = result.select_one('.search-result-title').get_text(strip=True)
                snippet = result.select_one('.search-result-snippet').get_text(strip=True)
                link = result.select_one('a')['href']
                results.append(f"{title}: {snippet} (Link: {base_url}{link})")
            return results
        else:
            logging.error(f"Error scraping Erasmushogeschool: HTTP {response.status_code}")
            return []
    except Exception as e:
        logging.error(f"Error scraping Erasmushogeschool: {e}")
        return []

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.json.get('query')
    if not query:
        return jsonify({"error": "No query provided"}), 400

    try:
        results = search_client.search(search_text=query, top=10)  # Limit the number of search results
        documents = [doc for doc in results]
        return jsonify(documents)
    except Exception as e:
        logging.error(f"Error during search: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/ask', methods=['POST'])
def ask():
    query = request.json.get('query')
    if not query:
        return jsonify({"error": "No query provided"}), 400

    try:
        # Zoek in Azure Cognitive Search
        search_results = search_client.search(search_text=query, top=10)  # Limit the number of search results
        documents = [doc for doc in search_results]

        # Filter documenten om alleen die van EHB te behouden
        relevant_documents = [doc for doc in documents if
                              'EHB' in doc.get('description', '') or 'Erasmushogeschool' in doc.get('description', '')]

        # Als geen relevante documenten gevonden worden, gebruik data uit lokale HTML-bestanden en blobs
        if not relevant_documents:
            local_html_data = load_html_files()
            relevant_documents = [doc for doc in local_html_data if
                                  'EHB' in doc.get('content', '') or 'Erasmushogeschool' in doc.get('content', '')]

            if not relevant_documents:
                blob_data = load_blob_data()
                relevant_documents = [doc for doc in blob_data if
                                      'EHB' in doc.get('content', '') or 'Erasmushogeschool' in doc.get('content', '')]

        if not relevant_documents:
            # Als nog steeds geen relevante documenten gevonden worden, gebruik web scraping of OpenAI
            scraped_data = scrape_erasmushogeschool(query)
            if not scraped_data:
                # Gebruik OpenAI om een antwoord te genereren
                prompt = f"Beantwoord de volgende vraag zo goed mogelijk, aangezien er geen specifieke informatie over EHB gevonden is:\n\nVraag: {query}\n\nGedetailleerd antwoord:"
                response = openai.Completion.create(
                    engine="gpt-35-turbo",
                    prompt=prompt,
                    max_tokens=500,
                    n=1,
                    stop=["\n"]
                )
                answer = response.choices[0].text.strip()
                return jsonify({"answer": answer})

            return jsonify({"answer": "Geen relevante informatie gevonden in EHB, maar hier zijn enkele resultaten van de Erasmushogeschool website:", "results": scraped_data})

        # Beperk het aantal documenten en truncate lange teksten
        max_docs = 20
        limited_documents = relevant_documents[:max_docs]
        context = " ".join(
            [f"{doc.get('name', 'Unknown')}: {truncate_text(doc.get('content', 'No content'))}" for doc in limited_documents])

        prompt = f"Gebruik de volgende informatie om de vraag te beantwoorden met een gedetailleerd antwoord:\n\n{context}\n\nVraag: {query}\n\nGedetailleerd antwoord:"

        response = openai.Completion.create(
            engine="gpt-35-turbo",  # Gebruik de juiste deployment name
            prompt=prompt,
            max_tokens=500,
            n=1,
            stop=["\n"]
        )

        answer = response.choices[0].text.strip()
        return jsonify({"answer": answer})
    except Exception as e:
        logging.error(f"Error during ask: {e}")
        return jsonify({"error": str(e)}), 500

def preload_blob_data():
    load_blob_data()
    logging.info("Preloaded blob data")

if __name__ == '__main__':
    # Preload blob data in a separate thread
    threading.Thread(target=preload_blob_data).start()
    app.run(debug=True)
