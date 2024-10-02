import requests
import base64

URL_BASE= "http://localhost:8001"

# URL del servidor FastAPI donde está corriendo el endpoint /update/
url = URL_BASE+"/update/"

# Ruta del archivo .p12 que se enviará
p12_file_path = ""

# Contraseña que se enviará
password = ""

# Leer el archivo .p12 y codificarlo en base64
with open(p12_file_path, "rb") as f:
    file_data = f.read()
    file_base64 = base64.b64encode(file_data).decode('utf-8')

# Crear el payload que se enviará en el cuerpo de la solicitud
payload = {
    "file": file_base64,
    "pass": password
}

# Hacer la solicitud POST al endpoint /update/
response = requests.post(url, json=payload)

# Imprimir la respuesta del servidor
print(f"Status Code: {response.status_code}")
print("Response:", response.json())

url = URL_BASE+"/ruc/"

# Lista de RUCs a verificar
rucs = [
    "4303489",
    "43034890"
]

# Hacer la solicitud GET por cada RUC en la lista
for ruc in rucs:
    response = requests.get(f"{url}{ruc}")
    
    # Imprimir la respuesta del servidor
    print(f"Verificando RUC: {ruc}")
    print(f"Status Code: {response.status_code}")
    print("Response:", response.json())
    print("-" * 40)  # Separador entre las respuestas