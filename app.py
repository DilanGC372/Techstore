
import os
from pathlib import Path

from flask import Flask, render_template, request

from productos_demo import PRODUCTOS_DEMO
from api_accesorios import (
    ErrorCatalogo,
    obtener_accesorios,
    obtener_computadoras,
)


# Vercel publica public/ desde la raiz.
# Flask local utiliza las mismas rutas para los archivos estaticos.
app = Flask(__name__, static_folder="public", static_url_path="")


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
    """Obliga a consultar Flask al recargar un catalogo."""
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
# PRESENTACION DEL CATALOGO
# --------------------------------------------------

def mostrar_catalogo(
    categoria,
    titulo,
    introduccion,
    fuente=None,
    demo=True,
    error=None,
):
    """Prepara unicamente los productos solicitados."""
    productos = []

    # Ilustraciones genericas disponibles.
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

        # Las imagenes pertenecen al frontend, no a EC2.
        ruta = producto.get("imagen_url") or ""
        archivo = ruta.removeprefix("/public/")
        raiz = Path(app.static_folder).resolve()

        try:
            destino = (raiz / archivo).resolve()

            imagen_local = (
                ruta.startswith("/public/images/")
                and destino.is_relative_to(raiz / "images")
                and destino.is_file()
            )

        except (OSError, ValueError):
            imagen_local = False

        if imagen_local:
            producto["imagen_archivo"] = archivo
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
        # La clave se obtiene del entorno del servidor.
        # Nunca se envia al navegador.
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
