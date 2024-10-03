from util.sifen_api import SifenApi
from fastapi.responses import JSONResponse
import uvicorn
import requests
from fastapi import FastAPI, UploadFile, File, HTTPException
import base64
import json
from urllib.parse import urlparse
import os
from decouple import config
app = FastAPI()

P12_FOLDER = "./p12/"

set_client = SifenApi()

def calcular_dv_11(p_numero: str) -> int:
    # Calcular el dígito verificador - RUC (módulo 11)
    p_basemax = 9
    v_numero_al = ""
    
    # Extraer solo los números, y convertir caracteres a números si no son dígitos
    for v_caracter in p_numero:
        if '0' <= v_caracter <= '9':
            v_numero_al += v_caracter
        else:
            v_numero_al += str(ord(v_caracter))  # Convertir no dígitos a su valor numérico

    k = 2
    v_total = 0
    i = len(v_numero_al) - 1

    # Recorrer el string de derecha a izquierda
    while i >= 0:
        k = 2 if k > p_basemax else k
        v_numero_aux = int(v_numero_al[i])  # Convertir el carácter a entero
        v_total += v_numero_aux * k
        k += 1
        i -= 1

    # Cálculo del módulo 11
    v_resto = v_total % 11
    v_digit = 11 - v_resto if v_resto > 1 else 0

    return v_digit

@app.get("/ruc/{documento}")
def verificar_documento(documento: str):
    respuesta = {
        "success": False,
        "result": {
            "respuesta_codigo": "999",
            "respuesta_mensaje": "Servidor SIFEN no responde",
        }
    }
    
    if not os.path.exists(P12_FOLDER):
            os.makedirs(P12_FOLDER)
            
    try:
        p12_file_path = os.path.join(P12_FOLDER, "file.p12")
        if not os.path.exists(p12_file_path):
            raise HTTPException(
                status_code=400, detail="Archivo .p12 no encontrado")

        # Leer el contenido del archivo key.txt que contiene la contraseña
        key_file_path = os.path.join(P12_FOLDER, "key.txt")
        if not os.path.exists(key_file_path):
            raise HTTPException(
                status_code=400, detail="Archivo key.txt no encontrado")

        with open(key_file_path, "r") as f:
            cert_pass = f.read().strip()

        # Llamada al cliente Sifen con el archivo .p12 y la contraseña
        resultado = set_client.consulta_ruc(
            id=0,
            ruc=documento,
            env="prod",
            certificado=p12_file_path,
            passphase=cert_pass,
            config=None
        )
        
        print(resultado)

        if resultado != None and resultado['success']:
            respuesta['result']['respuesta_codigo'] = resultado['data']['ns2:rResEnviConsRUC']['ns2:dCodRes']
            respuesta['result']['respuesta_mensaje'] = resultado['data']['ns2:rResEnviConsRUC']['ns2:dMsgRes']
            try:
                respuesta['result']['ruc_razonsocial'] = resultado['data']['ns2:rResEnviConsRUC']['ns2:xContRUC']['ns2:dRazCons']
                respuesta['result']['ruc_estado'] = resultado['data']['ns2:rResEnviConsRUC']['ns2:xContRUC']['ns2:dDesEstCons']
                respuesta['result']['ruc_ruc'] = "{}-{}".format(documento, calcular_dv_11(documento))
                respuesta['success'] = True
            except:
                pass

    except:
        respuesta['result']['respuesta_codigo'] = "999"
        respuesta['result']['respuesta_mensaje'] = "Archivo .p12 o Contraseña incorrectos"

    return JSONResponse(content=respuesta)


@app.post("/update/")
def update_certificate(body: dict):
    try:
        # Obtener los datos del archivo y la contraseña del cuerpo de la solicitud
        file_base64 = body.get("file")
        password = body.get("pass")

        if not file_base64 or not password:
            raise HTTPException(
                status_code=400, detail="Archivo o contraseña no proporcionados")

        # Decodificar el archivo base64
        file_data = base64.b64decode(file_base64)

        # Guardar el archivo .p12
        p12_file_path = os.path.join(P12_FOLDER, "file.p12")
        with open(p12_file_path, "wb") as f:
            f.write(file_data)

        # Guardar la contraseña en key.txt
        key_file_path = os.path.join(P12_FOLDER, "key.txt")
        with open(key_file_path, "w") as f:
            f.write(password)

        return JSONResponse(content={"success": True, "message": "Archivo y contraseña actualizados correctamente."})

    except Exception as e:
        return JSONResponse(content={"success": False, "message": str(e)})


if __name__ == "__main__":
    if "DYNO" in os.environ:
        workers = int(os.environ.get("WEB_CONCURRENCY", 1))
        timeout = int(os.environ.get("WEB_TIMEOUT", 120))
        uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get(
            "PORT", 8001)), workers=workers, timeout_keep_alive=timeout)
    else:
        uvicorn.run(app, host="0.0.0.0", port=int(
            os.environ.get("PORT", 8001)))
