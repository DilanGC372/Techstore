"""Contrato HTTP, páginas y errores sin acceder a AWS ni leer .env."""
import copy
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

from app import app


PRODUCTO = {
    "id": 6, "nombre": "Teclado mecanico RGB", "categoria": "Accesorio",
    "marca": "Redragon", "precio": "899.00", "stock": 20,
    "descripcion": "Teclado mecánico con iluminación RGB",
    "imagen_url": "/public/images/accesorios/teclado-rgb.png",
}


class CatalogoTests(unittest.TestCase):
    def setUp(self):
        self.config = patch.dict(app.config, TESTING=True,
                                 ACCESORIOS_API_URL="http://api.example/api/accesorios",
                                 COMPUTADORAS_API_URL="http://api.example/computadoras")
        self.config.start()
        self.addCleanup(self.config.stop)
        logger = patch.object(app.logger, "warning")
        logger.start()
        self.addCleanup(logger.stop)
        self.client = app.test_client()

    def respuesta(self, datos, status=200):
        respuesta = MagicMock()
        respuesta.__enter__.return_value = respuesta
        respuesta.status = status
        respuesta.read.return_value = (datos if isinstance(datos, bytes)
                                      else json.dumps(datos).encode("utf-8"))
        return respuesta

    def pedir(self, datos, status=200):
        with patch("api_accesorios.urlopen", return_value=self.respuesta(datos, status)):
            return self.client.get("/accesorios")

    def verificar_error(self, respuesta):
        self.assertEqual(respuesta.status_code, 503)
        html = respuesta.get_data(as_text=True)
        self.assertIn("No pudimos cargar los accesorios", html)
        self.assertIn("Volver a intentar", html)
        self.assertNotIn('class="product-card"', html)
        self.assertNotIn("Catálogo de demostración", html)
        self.assertNotIn("Todavía no hay productos", html)
        self.assertNotIn("api.example", html)

    def test_catalogo_real_precio_e_imagen_local(self):
        producto = {**PRODUCTO, "precio": "1299.50", "stock": 0}
        respuesta = self.pedir({"productos": [producto]})
        self.assertEqual(respuesta.status_code, 200)
        html = respuesta.get_data(as_text=True)
        self.assertIn("$1,299.50 MXN", html)
        self.assertIn("Agotado", html)
        self.assertIn('src="/public/images/accesorios/teclado-rgb.png"', html)
        self.assertNotIn("de ejemplo", html)
        self.assertNotIn("api.example", html)
        with self.client.get(PRODUCTO["imagen_url"]) as imagen:
            self.assertEqual(imagen.status_code, 200)

    def test_inicio_no_consulta_api(self):
        with patch("api_accesorios.urlopen", side_effect=AssertionError("Consulta no esperada")) as abrir:
            self.assertEqual(self.client.get("/").status_code, 200)
            abrir.assert_not_called()

    def test_catalogo_real_de_computadoras(self):
        computadora = {**PRODUCTO, "id": 1, "nombre": "Laptop IdeaPad 3",
                       "categoria": "Computadora", "marca": "Lenovo",
                       "precio": 12499.0, "stock": 10,
                       "imagen_url": "/public/images/computadoras/laptop-ideapad.png"}
        with patch("api_accesorios.urlopen",
                   return_value=self.respuesta({"categoria": "Computadora",
                                                "total": 1,
                                                "productos": [computadora]})):
            respuesta = self.client.get("/computadoras")
        self.assertEqual(respuesta.status_code, 200)
        html = respuesta.get_data(as_text=True)
        self.assertIn("$12,499.00 MXN", html)
        self.assertIn('src="/public/images/computadoras/laptop-ideapad.png"', html)
        self.assertNotIn("de ejemplo", html)

    def test_error_de_computadoras_no_muestra_demo(self):
        with patch("api_accesorios.urlopen", side_effect=URLError("fallo")):
            respuesta = self.client.get("/computadoras")
        self.assertEqual(respuesta.status_code, 503)
        html = respuesta.get_data(as_text=True)
        self.assertIn("No pudimos cargar las computadoras", html)
        self.assertNotIn('class="product-card"', html)

    def test_lista_vacia_no_es_fallo(self):
        respuesta = self.pedir({"productos": []})
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Todavía no hay productos", respuesta.get_data(as_text=True))

    def test_fallos_de_red_y_http_sin_datos_demo(self):
        errores = [TimeoutError(), URLError("fallo privado"),
                   HTTPError("http://api.example", 500, "detalle privado", {}, None)]
        for error in errores:
            with self.subTest(error=type(error).__name__):
                with patch("api_accesorios.urlopen", side_effect=error):
                    self.verificar_error(self.client.get("/accesorios"))
        self.verificar_error(self.pedir({"productos": [PRODUCTO]}, status=204))

    def test_url_ausente_o_invalida(self):
        for url in ("", "file:///archivo", "http://[", "https://"):
            with self.subTest(url=url), patch.dict(app.config, ACCESORIOS_API_URL=url):
                self.verificar_error(self.client.get("/accesorios"))

    def test_respuestas_invalidas(self):
        for datos in (b"<html>Error</html>", {}, [], {"productos": {}},
                      {"productos": [None]}, {"productos": [PRODUCTO, PRODUCTO]}):
            with self.subTest(datos=datos):
                self.verificar_error(self.pedir(datos))

    def test_campos_invalidos(self):
        casos = [("precio", "NaN"), ("precio", "Infinity"), ("precio", "incorrecto"),
                 ("precio", "-1"), ("stock", "20"), ("stock", -1), ("id", True),
                 ("nombre", None), ("categoria", "Computadora"), ("imagen_url", [])]
        for campo, valor in casos:
            with self.subTest(campo=campo, valor=valor):
                self.verificar_error(self.pedir({"productos": [{**PRODUCTO, campo: valor}]}))

    def test_imagen_ausente_externa_o_fuera_de_directorio(self):
        for ruta in (None, "https://api.example/foto.png", "/public/images/../../app.py",
                     "/public/images/accesorios/no-existe.png"):
            with self.subTest(ruta=ruta):
                respuesta = self.pedir({"productos": [{**PRODUCTO, "imagen_url": ruta}]})
                self.assertEqual(respuesta.status_code, 200)
                self.assertIn('src="/public/images/imagen-pendiente.svg"',
                              respuesta.get_data(as_text=True))

    def test_texto_api_escapado_y_campos_opcionales(self):
        producto = {**PRODUCTO, "nombre": "<script>alert(1)</script>",
                    "descripcion": None, "imagen_url": None}
        respuesta = self.pedir({"productos": [producto]})
        html = respuesta.get_data(as_text=True)
        self.assertEqual(respuesta.status_code, 200)
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("Descripción pendiente", html)

    def test_consulta_http_con_tiempo_limitado(self):
        with patch("api_accesorios.urlopen", return_value=self.respuesta({"productos": []})) as abrir:
            self.client.get("/accesorios")
            args, kwargs = abrir.call_args
            self.assertEqual(args[0].full_url, app.config["ACCESORIOS_API_URL"])
            self.assertEqual(kwargs["timeout"], 8)

    def test_catalogos_no_se_guardan_en_cache(self):
        with patch("api_accesorios.urlopen",
                   return_value=self.respuesta({"productos": [PRODUCTO]})):
            respuesta = self.client.get("/accesorios")
        self.assertEqual(respuesta.headers["Cache-Control"], "no-store, max-age=0")
        self.assertEqual(respuesta.headers["Pragma"], "no-cache")

    def test_integracion_http_local(self):
        solicitudes = []

        class APIPrueba(BaseHTTPRequestHandler):
            def do_GET(self):
                solicitudes.append(self.path)
                body = json.dumps({"productos": [copy.deepcopy(PRODUCTO)]}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_args):
                pass

        servidor = ThreadingHTTPServer(("127.0.0.1", 0), APIPrueba)
        hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
        hilo.start()
        try:
            url = f"http://127.0.0.1:{servidor.server_port}/api/accesorios"
            with patch.dict(app.config, ACCESORIOS_API_URL=url):
                respuesta = self.client.get("/accesorios")
            self.assertEqual(respuesta.status_code, 200)
            self.assertIn("Teclado mecanico RGB", respuesta.get_data(as_text=True))
            self.assertEqual(solicitudes, ["/api/accesorios"])
        finally:
            servidor.shutdown()
            servidor.server_close()
            hilo.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
