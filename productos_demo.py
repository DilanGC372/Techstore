"""Datos locales tomados del SQL de ejemplo; no representan una consulta a RDS.

Los identificadores son de demostración. Los precios están en pesos mexicanos (MXN).
"""

from decimal import Decimal


# id, nombre, categoría, marca, precio, stock, descripción, archivo esperado.
_REGISTROS = [
    (1, "Laptop IdeaPad 3", "Computadora", "Lenovo", "12499.00", 10,
     "Laptop para estudiantes y trabajo.", "computadoras/laptop-ideapad.png"),
    (2, "Laptop Pavilion", "Computadora", "HP", "14999.00", 7,
     "Laptop para productividad y uso diario.", "computadoras/laptop-pavilion.png"),
    (3, "PC Gamer", "Computadora", "ASUS", "18999.00", 5,
     "Computadora de escritorio para videojuegos.", "computadoras/pc-gamer.png"),
    (4, "Laptop Aspire 5", "Computadora", "Acer", "11499.00", 8,
     "Laptop para actividades escolares y profesionales.", "computadoras/laptop-aspire.png"),
    (5, "MacBook Air", "Computadora", "Apple", "21999.00", 4,
     "Laptop ligera para productividad.", "computadoras/macbook-air.png"),
    (6, "Teclado mecanico RGB", "Accesorio", "Redragon", "899.00", 20,
     "Teclado mecanico con iluminacion RGB.", "accesorios/teclado-rgb.png"),
    (7, "Mouse inalambrico", "Accesorio", "Logitech", "499.00", 25,
     "Mouse inalambrico para computadora.", "accesorios/mouse-inalambrico.png"),
    (8, "Audifonos Gamer", "Accesorio", "HyperX", "1299.00", 12,
     "Audifonos para videojuegos con microfono.", "accesorios/audifonos-gamer.png"),
    (9, "Webcam HD", "Accesorio", "Logitech", "799.00", 15,
     "Camara web para videollamadas.", "accesorios/webcam-hd.png"),
    (10, "Memoria USB 64 GB", "Accesorio", "Kingston", "199.00", 30,
     "Memoria USB para almacenar archivos.", "accesorios/memoria-usb.png"),
    (11, "Monitor 24 pulgadas", "Computadora", "Samsung", "3299.00", 6,
     "Monitor para computadora de 24 pulgadas.", "computadoras/monitor-24.png"),
    (12, "Base enfriadora para laptop", "Accesorio", "Cooler Master", "649.00", 10,
     "Base para mejorar la ventilacion de una laptop.", "accesorios/base-enfriadora.png"),
]

PRODUCTOS_DEMO = [
    {
        "id": id_producto,
        "nombre": nombre,
        "categoria": categoria,
        "marca": marca,
        "precio": Decimal(precio),
        "stock": stock,
        "descripcion": descripcion,
        "imagen_url": f"/public/images/{archivo}",
    }
    for id_producto, nombre, categoria, marca, precio, stock, descripcion, archivo
    in _REGISTROS
]
