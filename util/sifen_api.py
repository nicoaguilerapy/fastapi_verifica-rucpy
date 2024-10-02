import requests
from requests_pkcs12 import Pkcs12Adapter
import xmltodict
import json
import zipfile
import base64
from io import BytesIO
import os


class SifenApi:
    
    def __init__(self):
        self.cert = None
        self.key = None

    def _handle_response(self, response, id, save):
        try:
            if response.status_code == 200:
                if response.text.startswith("<?xml"):
                    result = xmltodict.parse(response.text)
                    if save:
                        self.save_file(save, id, response.text)
                    result_data = result["env:Envelope"]["env:Body"]
                    result_data['id'] = id
                    return {"success": True, "data": result_data}
                elif response.text.startswith("<html>"):
                    raise ValueError("Error de la SIFEN BIG-IP logout page")
                else:
                    raise ValueError(response.text)
            else:
                raise ValueError("Error de conexión con la SIFEN")
        except Exception as e:
            return {"success": False, "error": str(e)}
        
    def abrir(self, certificado, passphase):
        # Cargar el archivo .p12
        self.cert = certificado
        self.key = passphase

    def normalize_xml(self, xml_str):
        # Normaliza la cadena XML (por si necesitas algún procesamiento)
        return xml_str

    def save_file(self, path, id, resultado):
        path = os.path.join(path, "{}.xml".format(id))
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(resultado)
            

    def consulta_ruc(self, id, ruc, env, certificado, passphase, config=None):
        default_config = {
            'debug': False,
            'timeout': 90000,
            'save_request': None,
            'save_response': None,
            'print':True
        }

        if config:
            default_config.update(config)

        self.abrir(certificado, passphase)

        url = "https://sifen.set.gov.py/de/ws/consultas/consulta-ruc.wsdl"
        if env == "test":
            url = "https://sifen-test.set.gov.py/de/ws/consultas/consulta-ruc.wsdl"

        if not self.cert or not self.key:
            raise ValueError("Antes debe Autenticarse")

        soap_xml_data = f"""<env:Envelope xmlns:env="http://www.w3.org/2003/05/soap-envelope">
                            <env:Header/>
                            <env:Body>
                                <rEnviConsRUC xmlns="http://ekuatia.set.gov.py/sifen/xsd">
                                    <dId>{id}</dId>
                                    <dRUCCons>{ruc}</dRUCCons>
                                </rEnviConsRUC>
                            </env:Body>
                        </env:Envelope>"""
        soap_xml_data = self.normalize_xml(soap_xml_data)

        if default_config['print']:
            print("soapXMLData", soap_xml_data)

        if default_config['save_request']:
            with open(os.path.join(default_config['save_request'], '{}.xml'.format(id), ), 'w') as file:
                file.write(soap_xml_data)

        session = requests.Session()
        session.mount(url, Pkcs12Adapter(
            pkcs12_filename=self.cert, pkcs12_password=self.key))

        response = session.post(url, data=soap_xml_data, headers={
            "User-Agent": "VerificaRuc",
            "Content-Type": "application/xml; charset=utf-8"
        }, timeout=default_config['timeout'])

        return self._handle_response(response, id, default_config['save_response'])
