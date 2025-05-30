# ferremas/webpay.py

import requests
import ferremas.webpay_config as config

HEADERS = {
    "Tbk-Api-Key-Id": config.COMMERCE_CODE,
    "Tbk-Api-Key-Secret": config.API_KEY,
    "Content-Type": "application/json"
}

import logging

logger = logging.getLogger(__name__)

def crear_transaccion(orden_id, sesion_id, monto):
    payload = {
    'buy_order': orden_id,
    'session_id': sesion_id,
    'amount': int(monto),  
    'return_url': config.RETURN_URL
}

    try:
        respuesta = requests.post(f"{config.WEBPAY_API_URL}/transactions", headers=HEADERS, json=payload)

        if respuesta.status_code in [200, 201]:
            return respuesta.json()
        else:
            logger.error(f"Error en solicitud a Webpay: {respuesta.status_code} - {respuesta.text}")
            return None

    except requests.exceptions.RequestException as e:
        logger.exception("Excepción al conectar con Webpay")
        return None

def confirmar_transaccion(token):
    try:
        respuesta = requests.put(f"{config.WEBPAY_API_URL}/transactions/{token}", headers=HEADERS)

        if respuesta.status_code in [200, 201]:
            return respuesta.json()
        else:
            print(f"Error en la confirmación: {respuesta.status_code}, {respuesta.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error HTTP al confirmar transacción: {e}")
        return None
