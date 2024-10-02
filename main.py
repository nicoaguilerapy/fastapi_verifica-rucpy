from util.sifen_api import SifenApi
from fastapi.responses import JSONResponse
import uvicorn
import requests
from fastapi import FastAPI
import redis
import json
from urllib.parse import urlparse
import os
from decouple import config
app = FastAPI()

cert_file = config("CERT")
cert_pass = config("PASS")

set_client = SifenApi()

@app.get("/ruc/{documento}")
def verificar_documento(documento: str):
    respuesta = {
        "success": False,
        "result": {
            "respuesta_codigo": "999",
            "respuesta_mensaje": "Servidor SIFEN no responde",
        }
    }
    
    try:
        resultado = set_client.consulta_ruc(
            id=0,
            ruc=documento,
            env="prod",
            certificado=cert_file,
            passphase=cert_pass,
            config=None
        )
        
        if resultado != None and resultado['success']:
            respuesta['result']['respuesta_codigo'] = resultado['data']['ns2:rResEnviConsRUC']['ns2:dCodRes']
            respuesta['result']['respuesta_mensaje'] = resultado['data']['ns2:rResEnviConsRUC']['ns2:dMsgRes']
            try:
                respuesta['result']['ruc_razonsocial'] = resultado['data']['ns2:rResEnviConsRUC']['ns2:xContRUC']['ns2:dRazCons']
                respuesta['result']['ruc_estado'] = resultado['data']['ns2:rResEnviConsRUC']['ns2:xContRUC']['ns2:dDesEstCons']
            except:
                pass
    
    except:
        respuesta['result']['respuesta_codigo'] = "999"
        respuesta['result']['respuesta_mensaje'] = "Archivo .p12 o Contraseña incorrectos"
    
    return JSONResponse(content=respuesta)


if __name__ == "__main__":
    if "DYNO" in os.environ:
        workers = int(os.environ.get("WEB_CONCURRENCY", 1))
        timeout = int(os.environ.get("WEB_TIMEOUT", 120))
        uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get(
            "PORT", 8001)), workers=workers, timeout_keep_alive=timeout)
    else:
        uvicorn.run(app, host="0.0.0.0", port=int(
            os.environ.get("PORT", 8001)))
