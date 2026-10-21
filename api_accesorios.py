
"""Cliente HTTP del catálogo. No accede a RDS ni lee archivos .env."""

import json
from decimal import Decimal, InvalidOperation
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

TIEMPO_ESPERA = 8
MAX_RESPUESTA = 2 * 1024 * 1024


class ErrorCatalogo(Exception):
    """La API no está disponible o no cumple el contrato del catálogo."""


def obtener_productos(url, categoria, api_key=None):
    try:
        destino = urlsplit(url or "")

        if destino.scheme not in {"http", "https"} or not destino.hostname:
            raise ErrorCatalogo("URL del catálogo sin configurar o inválida")

        # Preparar encabezados HTTP.
        encabezados = {
            "Accept": "application/json"
        }

        # Enviar la clave solamente cuando sea proporcionada.
        if api_key is not None:
            if not isinstance(api_key, str) or not api_key.strip():
                raise ErrorCatalogo("Clave de API inválida")

            # Evitar enviar credenciales por HTTP.
            if destino.scheme != "https":
                raise ErrorCatalogo("La autenticación requiere HTTPS")

            encabezados["X-API-Key"] = api_key

        solicitud = Request(url, headers=encabezados)

        with urlopen(solicitud, timeout=TIEMPO_ESPERA) as respuesta:
            if respuesta.status != 200:
                raise ErrorCatalogo("Estado HTTP inesperado")

            contenido = respuesta.read(MAX_RESPUESTA + 1)

        if len(contenido) > MAX_RESPUESTA:
            raise ErrorCatalogo("Respuesta demasiado grande")

        datos = json.loads(contenido)

        if not isinstance(datos, dict) or not isinstance(
            datos.get("productos"), list
        ):
            raise ErrorCatalogo("Lista de productos inválida")

        productos = []
        ids = set()

        for fila in datos["productos"]:
            if not isinstance(fila, dict):
                raise ErrorCatalogo("Producto inválido")

            for campo in ("nombre", "marca"):
                if not isinstance(fila.get(campo), str) or not fila[campo].strip():
                    raise ErrorCatalogo("Texto de producto inválido")

            if fila.get("categoria") != categoria:
                raise ErrorCatalogo("Categoría inesperada")

            if (
                type(fila.get("id")) is not int
                or fila["id"] <= 0
                or fila["id"] in ids
            ):
                raise ErrorCatalogo("Identificador inválido")

            if type(fila.get("stock")) is not int or fila["stock"] < 0:
                raise ErrorCatalogo("Existencias inválidas")

            for campo in ("descripcion", "imagen_url"):
                if (
                    fila.get(campo) is not None
                    and not isinstance(fila[campo], str)
                ):
                    raise ErrorCatalogo("Texto opcional inválido")

            precio = Decimal(str(fila.get("precio")))

            if (
                not precio.is_finite()
                or not 0 <= precio <= Decimal("99999999.99")
            ):
                raise ErrorCatalogo("Precio inválido")

            productos.append({
                **fila,
                "precio": precio.quantize(Decimal("0.01"))
            })

            ids.add(fila["id"])

        return productos

    except HTTPError as error:
        error.close()
        raise ErrorCatalogo("La API devolvió un error HTTP") from error

    except (
        URLError,
        OSError,
        HTTPException,
        ValueError,
        InvalidOperation,
    ) as error:
        raise ErrorCatalogo("No se pudo consultar el catálogo") from error


def obtener_accesorios(url, api_key=None):
    return obtener_productos(url, "Accesorio", api_key=api_key)


def obtener_computadoras(url):
    return obtener_productos(url, "Computadora")
