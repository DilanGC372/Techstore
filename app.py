import os
from pathlib import Path

from flask import Flask, render_template, request

from productos_demo import PRODUCTOS_DEMO
from api_accesorios import ErrorCatalogo, obtener_accesorios, obtener_computadoras

# Vercel publica el contenido de public/ desde la raíz; Flask local usa las
# mismas direcciones para que CSS, JavaScript e imágenes funcionen en ambos.
app = Flask(__name__, static_folder="public", static_url_path="")
app.config["ACCESORIOS_API_URL"] = os.environ.get(
    "ACCESORIOS_API_URL",
    "http://184.197.49.100:8000/api/accesorios",
)
app.config["COMPUTADORAS_API_URL"] = os.environ.get(
    "COMPUTADORAS_API_URL",
    "http://54.83.158.131:5000/computadoras",
)


@app.after_request
def evitar_cache_de_catalogos(respuesta):
    """Obliga a consultar Flask otra vez al recargar un catálogo."""
    if request.endpoint in {"accesorios", "computadoras"}:
        respuesta.headers["Cache-Control"] = "no-store, max-age=0"
        respuesta.headers["Pragma"] = "no-cache"
        respuesta.headers["Expires"] = "0"
    return respuesta


@app.route("/")
def index():
    """Devuelve la página principal de TechStore."""
    return render_template("index.html")


def mostrar_catalogo(categoria, titulo, introduccion, fuente=None, demo=True, error=None):
    """Prepara únicamente los productos de la categoría solicitada."""
    productos = []
    # Ilustraciones genéricas disponibles, no fotografías de esos modelos.
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
        # Las rutas de la API pertenecen al frontend, nunca al servidor EC2.
        ruta = producto.get("imagen_url") or ""
        archivo = ruta.removeprefix("/public/")
        raiz = Path(app.static_folder).resolve()
        try:
            destino = (raiz / archivo).resolve()
            imagen_local = (ruta.startswith("/public/images/")
                            and destino.is_relative_to(raiz / "images")
                            and destino.is_file())
        except (OSError, ValueError):
            imagen_local = False
        if imagen_local:
            producto["imagen_archivo"] = archivo
            producto["imagen_nota"] = "Imagen ilustrativa del producto."
        elif demo and producto["id"] in ilustraciones:
            producto["imagen_archivo"] = ilustraciones[producto["id"]]
            producto["imagen_nota"] = "Imagen ilustrativa; no corresponde al modelo exacto."
        else:
            producto["imagen_archivo"] = "images/imagen-pendiente.svg"
            producto["imagen_nota"] = "Imagen pendiente"
        productos.append(producto)
    return render_template(
        "catalogo.html", productos=productos, titulo=titulo,
        introduccion=introduccion, demo=demo, error=error,
    )


@app.route("/computadoras")
def computadoras():
    error = None
    try:
        productos = obtener_computadoras(app.config["COMPUTADORAS_API_URL"])
    except ErrorCatalogo:
        app.logger.warning("No se pudo cargar el catálogo de computadoras desde la API.")
        productos = []
        error = "No pudimos cargar las computadoras. Inténtalo de nuevo en unos momentos."
    pagina = mostrar_catalogo(
        "Computadora", "Computadoras",
        "Explora laptops, equipos de escritorio y monitores para tu espacio.",
        fuente=productos, demo=False, error=error,
    )
    return pagina, 503 if error else 200


@app.route("/accesorios")
def accesorios():
    error = None
    try:
        productos = obtener_accesorios(app.config["ACCESORIOS_API_URL"])
    except ErrorCatalogo:
        app.logger.warning("No se pudo cargar el catálogo de accesorios desde la API.")
        productos = []
        error = "No pudimos cargar los accesorios. Inténtalo de nuevo en unos momentos."
    pagina = mostrar_catalogo(
        "Accesorio", "Accesorios",
        "Encuentra los complementos para estudiar, trabajar y disfrutar de tu equipo.",
        fuente=productos, demo=False, error=error,
    )
    return pagina, 503 if error else 200


if __name__ == "__main__":
    # Durante el desarrollo, vuelve a leer el HTML si cambia en el disco.
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    # Servidor de desarrollo, accesible únicamente desde este equipo.
    app.run(host="127.0.0.1", port=5000, load_dotenv=False)
