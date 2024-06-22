import tls_client
import requests
import json
import uuid
import os
import zipfile
import tempfile
from tqdm import tqdm

session = tls_client.Session(
    client_identifier="safari_ios_15_5",
    random_tls_extension_order=True
)

email = input("Email: ")
password = input("Password: ")

login_url = "https://npmoffline.sanoma.it/mcs/api/v1/login"

payload = json.dumps({
    "id": email,
    "password": password
})

headers = {
    'Content-Type': 'application/json',
    'X-Timezone-Offset': '+0200'
}

login = session.post(
    login_url,
    headers=headers,
    json=payload
)

token = login.json().get('result', {}).get('data', {}).get('access_token', None)

url_libri = "https://npmoffline.sanoma.it/mcs/api/v1/books?app=true"
headers_libri = {
    "X-Auth-Token": f"Bearer {token}"
}

libri = requests.get(url=url_libri, headers=headers_libri)
data = json.loads(libri.text)

titoli_id = []

for item in data['result']['data']:
    titolo = item['name']
    id = item['gedi']
    titoli_id.append((titolo, id))

for titolo, id in titoli_id:
    print(f"\nTitle: {titolo} | ID: {id}")

id_scelto = input("\nID : ")

print("\nFetching data...\n")

random_uuid = uuid.uuid4()
uuid_u = str(random_uuid).upper()

url_libri_download = f"https://npmoffline.sanoma.it/mcs/users/{email}/products/books/{id_scelto}?app=true&light=true&uuid={uuid_u}"
headers_libri_download = {
    "X-Auth-Token": f"Bearer {token}"
}

libri_download = requests.get(url=url_libri_download, headers=headers_libri_download)
url_download = libri_download.json().get('result', {}).get('data', {}).get('url_download', None)

current_directory = os.path.dirname(os.path.abspath(__file__))

def download_with_progress(url_download, filepath):
    response = requests.get(url_download, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    chunk_size = 1024
    with open(filepath, 'wb') as file, tqdm(
        total=total_size,
        unit='B',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(chunk_size=chunk_size):
            file.write(data)
            bar.update(len(data))

with tempfile.TemporaryDirectory() as tempdir:
    zip_file_path = os.path.join(tempdir, 'downloaded_file.zip')
    
    download_with_progress(url_download, zip_file_path)
    
    extract_folder = os.path.join(tempdir, 'extracted_data')
    os.makedirs(extract_folder, exist_ok=True)
    
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_folder)
    
    master_json_path = os.path.join(extract_folder, 'data', 'master.json')
    with open(master_json_path, 'r') as json_file:
        master_data = json.load(json_file)


print("\nDownloading pdf...\n")

def trova_link_pdf(master_data):
    for unit in master_data['units']:
        if 'chapters' in unit and len(unit['chapters']) > 0:
            for chapter in unit['chapters']:
                if 'pages' in chapter and len(chapter['pages']) > 0:
                    for page in chapter['pages']:
                        if 'unit' in page and 'book' in page['unit'] and 'pdf' in page['unit']['book']:
                            return page['unit']['book']['pdf']

pdf_url = trova_link_pdf(master_data)

pdf_na = master_data['name']
pdf_nam = pdf_na.replace("/", "-")
pdf_name = f"{pdf_nam}.pdf"

pdf_finale = os.path.join(current_directory, pdf_name)
download_with_progress(pdf_url, pdf_finale)

print("\nDone! You'll find the PDF in the directory of the script.")