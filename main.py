import requests
from fastapi import FastAPI
import redis
import json
from urllib.parse import urlparse
import os
from decouple import config
app = FastAPI()
import uvicorn
from fastapi.responses import JSONResponse

redis_url = config("REDIS_URL")
api_key = config("API_KEY")
api = config("API")

def guardar_en_redis(clave, valor):
    redis_client.setex(clave, 7 * 24 * 60 * 60, valor)
    
redis_url = urlparse(redis_url)
redis_host = redis_url.hostname
redis_port = redis_url.port
redis_password = redis_url.password

# Configurar la conexión con Redis
redis_client = redis.Redis(host=redis_host, port=redis_port, password=redis_password)

@app.get("/ruc/{documento}")
def verificar_documento(documento: str):
    if redis_client.exists(documento):
        resultado_json = redis_client.get(documento)
        resultado_dict = json.loads(resultado_json)
        return JSONResponse(content=resultado_dict)
    else:
        headers = {
            'Authorization': 'Bearer api_key_'+api_key  # Reemplaza api_key_XXXXXXX con tu API key válida
        }
        url = f'{api}/ruc/{documento}'
        response = requests.post(url, headers=headers)

        if response.status_code == 200:
            resultado_json = response.json()
            guardar_en_redis(documento, json.dumps(resultado_json))
            return JSONResponse(content=resultado_json)

        else:
            error_response = {
                "success": False,
                "result": {
                    "respuesta_codigo": "999",
                    "respuesta_mensaje": "Servidor SIFEN no responde"
                }
            }
            return JSONResponse(content=error_response)
        
@app.get("/test")
def test_endpoint():
    headers = {
        'Authorization': 'Bearer api_key_'+api_key  # Reemplaza api_key_XXXXXXX con tu API key válida
    }
    url = f'{api}/test'
    response = requests.get(url, headers=headers)
    print(url)
    print(headers)
    print(response.status_code)
    if response.status_code == 200:
        resultado_json = {
                "success": True,
                "result": {
                    "respuesta_mensaje": response.text
                }
        }
        return JSONResponse(content=resultado_json)
    else:
        error_response = {
                "success": False,
                "result": {
                    "respuesta_codigo": "999",
                    "respuesta_mensaje": "Servidor SIFEN no responde"
                }
            }
        return JSONResponse(content=error_response)

        
if __name__ == "__main__":
    if config("DEPLOY") == "N":
        uvicorn.run(app, host="0.0.0.0", port=8001)
    else:
        if "DYNO" in os.environ:
            workers = int(os.environ.get("WEB_CONCURRENCY", 1))
            timeout = int(os.environ.get("WEB_TIMEOUT", 120))
            uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), workers=workers, timeout_keep_alive=timeout)
        else:
            uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))