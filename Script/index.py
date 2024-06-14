from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import SearchIndex, SimpleField, SearchableField
from azure.core.credentials import AzureKeyCredential

# Configuratie
search_service_name = "hamzasearch"
search_key = "b0Kqp7pnOtjS3vHZprCNejAHlwSv7k0DIk1yhZItSOAzSeAOew0Q"
index_name = "openaiindex"

# Maak een SearchIndexClient aan
index_client = SearchIndexClient(
    endpoint=f"https://{search_service_name}.search.windows.net",
    credential=AzureKeyCredential(search_key)
)

# Haal de bestaande index op
index = index_client.get_index(index_name)

# Controleer welke velden al aanwezig zijn
existing_field_names = {field.name for field in index.fields}

# Voeg alleen nieuwe velden toe als ze nog niet bestaan
new_fields = [
    SimpleField(name="id", type="Edm.String", key=True),
    SearchableField(name="courseName", type="Edm.String", searchable=True),
    SearchableField(name="description", type="Edm.String", searchable=True),
    SearchableField(name="careerOpportunities", type="Edm.String", searchable=True)
]

for field in new_fields:
    if field.name not in existing_field_names:
        index.fields.append(field)

# Werk de index bij
index_client.create_or_update_index(index)

print(f"Index '{index_name}' bijgewerkt met nieuwe velden.")
