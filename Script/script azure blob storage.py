from azure.storage.blob import BlobServiceClient

# Verbindingstekst
connect_str = "DefaultEndpointsProtocol=https;AccountName=hamzastorag;AccountKey=3rEtDek+sP0tssRHLRjIYZARl2j3FHzKSEINZiJ7vCy9mI+wMBOZUfq3ELkVkMLWP53Fs4R1c9a8+AStHJ/euQ==;EndpointSuffix=core.windows.net"

# Instellen van de BlobServiceClient
blob_service_client = BlobServiceClient.from_connection_string(connect_str)
container_name = "ehbdata"  # Vervang door de naam van je container

# Controleer of de container bestaat, zo niet, maak de container aan
container_client = blob_service_client.get_container_client(container_name)
try:
    container_client.get_container_properties()
    print(f"Container '{container_name}' bestaat al.")
except Exception as e:
    print(f"Container '{container_name}' bestaat niet. Aanmaken van container...")
    container_client.create_container()
    print(f"Container '{container_name}' succesvol aangemaakt.")

# Uploaden van het JSON-bestand erasmushogeschool.json
blob_name = "erasmushogeschool.json"  # Zorg ervoor dat de blobnaam geen ongeldige tekens bevat
file_path = "../erasmushogeschool.json"  # Voeg het lokale pad toe van je bestand

blob_client = container_client.get_blob_client(blob_name)
with open(file_path, 'rb') as data:
    blob_client.upload_blob(data, overwrite=True)
print(f"Data van '{file_path}' succesvol geüpload naar blob '{blob_name}'.")
