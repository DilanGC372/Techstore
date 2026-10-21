
import os
from pathlib import Path, PurePosixPath

from flask import Flask, render_template, request

from productos_demo import PRODUCTOS_DEMO
from api_accesorios import (
    ErrorCatalogo,
    obtener_accesorios,
    obtener_computadoras,
)


# --------------------------------------------------
# CONFIGURACION DE FLASK
# --------------------------------------------------

# Vercel publica public/ desde la raiz del sitio.
# Flask local conserva las mismas rutas.
app = Flask(
    __name__,
    static_folder="public",
    static_url_path="",
)


# --------------------------------------------------
# CONFIGURACION DE LAS APIS
# --------------------------------------------------

app.config["ACCESORIOS_API_URL"] = os.environ.get(
    "ACCESORIOS_API_URL",
    "https://techstore-accesorios.duckdns.org/api/accesorios",
)

app.config["COMPUTADORAS_API_URL"] = os.environ.get(
    "COMPUTADORAS_API_URL",
    "http://54.83.158.131:5000/computadoras",
)


# --------------------------------------------------
# CONTROL DE CACHE
# --------------------------------------------------

@app.after_request
def evitar_cache_de_catalogos(respuesta):
    """Evita utilizar catalogos HTML almacenados en cache."""

    if request.endpoint in {"accesorios", "computadoras"}:
        respuesta.headers["Cache-Control"] = "no-store, max-age=0"
        respuesta.headers["Pragma"] = "no-cache"
        respuesta.headers["Expires"] = "0"

    return respuesta


# --------------------------------------------------
# PAGINA PRINCIPAL
# --------------------------------------------------

@app.route("/")
def index():
    """Devuelve la pagina principal de TechStore."""
    return render_template("index.html")


# --------------------------------------------------
# VALIDACION SEGURA DE IMAGENES
# --------------------------------------------------

def obtener_imagen_local(imagen_url):
    """
    Convierte rutas locales de la API a rutas publicas.

    Ejemplo:

    Entrada:
        /public/images/accesorios/teclado-rgb.png

    Salida:
        images/accesorios/teclado-rgb.png

    No admite URLs externas, rutas absolutas arbitrarias,
    barras invertidas ni recorridos de directorios.
    """

    if not isinstance(imagen_url, str):
        return None

    if not imagen_url.startswith("/public/images/"):
        return None

    ruta = imagen_url.removeprefix("/public/")

    if (
        "\\" in ruta
        or "?" in ruta
        or "#" in ruta
        or "%" in ruta
        or any(ord(caracter) < 32 for caracter in ruta)
    ):
        return None

    partes = PurePosixPath(ruta).parts

    if (
        len(partes) < 3
        or partes[0] != "images"
        or partes[1] not in {"accesorios", "computadoras"}
        or any(parte in {"", ".", ".."} for parte in ruta.split("/"))
    ):
        return None

    # Verificar extension de imagen permitida.
    extensiones = {".png", ".jpg", ".jpeg", ".webp", ".svg"}

    if PurePosixPath(ruta).suffix.lower() not in extensiones:
        return None

    # No comprobamos is_file() en Vercel.
    # Los archivos de public/ son publicados por separado.
    return ruta


# --------------------------------------------------
# PREPARACION DEL CATALOGO
# --------------------------------------------------

def mostrar_catalogo(
    categoria,
    titulo,
    introduccion,
    fuente=None,
    demo=True,
    error=None,
):
    """Prepara los productos de la categoria solicitada."""

    productos = []

    # Ilustraciones genericas para el modo demostracion.
    ilustraciones = {
        1: "images/laptop-plateada.png",
        2: "images/laptop-plateada.png",
        4: "images/laptop-plateada.png",
        5: "images/laptop-plateada.png",
        8: "images/audifonos-diadema.png",
    }

    for original in (PRODUCTOS_DEMO if fuente is None else fuente):

        if original["categoria"] != categoria:
            continue

        producto = original.copy()

        # Recuperar la ruta de imagen proporcionada por la API.
        ruta_imagen = producto.get("imagen_url")

        imagen_local = obtener_imagen_local(ruta_imagen)

        if imagen_local:
            producto["imagen_archivo"] = imagen_local
            producto["imagen_nota"] = (
                "Imagen ilustrativa del producto."
            )

        elif demo and producto["id"] in ilustraciones:
            producto["imagen_archivo"] = ilustraciones[producto["id"]]
            producto["imagen_nota"] = (
                "Imagen ilustrativa; no corresponde "
                "al modelo exacto."
            )

        else:
            producto["imagen_archivo"] = (
                "images/imagen-pendiente.svg"
            )
            producto["imagen_nota"] = "Imagen pendiente"

        productos.append(producto)

    return render_template(
        "catalogo.html",
        productos=productos,
        titulo=titulo,
        introduccion=introduccion,
        demo=demo,
        error=error,
    )


# --------------------------------------------------
# CATALOGO DE COMPUTADORAS
# --------------------------------------------------

@app.route("/computadoras")
def computadoras():

    error = None

    try:
        productos = obtener_computadoras(
            app.config["COMPUTADORAS_API_URL"]
        )

    except ErrorCatalogo:
        app.logger.warning(
            "No se pudo cargar el catalogo "
            "de computadoras desde la API."
        )

        productos = []
        error = (
            "No pudimos cargar las computadoras. "
            "Inténtalo de nuevo en unos momentos."
        )

    pagina = mostrar_catalogo(
        "Computadora",
        "Computadoras",
        "Explora laptops, equipos de escritorio "
        "y monitores para tu espacio.",
        fuente=productos,
        demo=False,
        error=error,
    )

    return pagina, 503 if error else 200


# --------------------------------------------------
# CATALOGO DE ACCESORIOS CON AUTENTICACION
# --------------------------------------------------

@app.route("/accesorios")
def accesorios():

    error = None

    try:
        api_key = os.environ.get("TECHSTORE_API_KEY")

        if not api_key or not api_key.strip():
            raise ErrorCatalogo(
                "La autenticacion de accesorios no esta configurada"
            )

        productos = obtener_accesorios(
            app.config["ACCESORIOS_API_URL"],
            api_key=api_key,
        )

    except ErrorCatalogo:
        app.logger.warning(
            "No se pudo cargar el catalogo "
            "de accesorios desde la API."
        )

        productos = []
        error = (
            "No pudimos cargar los accesorios. "
            "Inténtalo de nuevo en unos momentos."
        )

    pagina = mostrar_catalogo(
        "Accesorio",
        "Accesorios",
        "Encuentra los complementos para estudiar, "
        "trabajar y disfrutar de tu equipo.",
        fuente=productos,
        demo=False,
        error=error,
    )

    return pagina, 503 if error else 200


# --------------------------------------------------
# EJECUCION LOCAL
# --------------------------------------------------

if __name__ == "__main__":

    app.config["TEMPLATES_AUTO_RELOAD"] = True

    app.run(
        host="127.0.0.1",
        port=5000,
        load_dotenv=False,
    )
