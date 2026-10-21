# TechStore: catálogo local

Flask consulta las dos APIs desde el servidor y genera `/accesorios` y
`/computadoras`.
El navegador recibe HTML e imágenes de TechStore; no llama directamente a EC2.

## Iniciar en PowerShell

```powershell
Set-Location 'C:\Users\dilan\Desktop\Decimo\Escalamiento de Redes\Tecstore'
.\.venv\Scripts\python.exe app.py
```

Abre http://127.0.0.1:5000/accesorios. Si necesitas instalar las dependencias:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Las direcciones actuales de ambas APIs están configuradas como valores
predeterminados en `app.py`, por lo que no necesitas definir variables para las
pruebas locales. `ACCESORIOS_API_URL` y `COMPUTADORAS_API_URL` siguen disponibles
para reemplazar esas direcciones durante un despliegue. Flask las lee al iniciar:
reinicia el proceso si cambias un valor. No contienen contraseñas. `.env.example`
es solo una referencia; el proyecto no lee `.env` y no necesita credenciales RDS.

## Comprobar la conexión real

Desde otra terminal de tu computadora:

```powershell
Invoke-RestMethod -Uri 'http://54.164.87.181:8000/api/accesorios' -TimeoutSec 8
Invoke-RestMethod -Uri 'http://54.83.158.131:5000/computadoras' -TimeoutSec 8
```

Si ambas devuelven `productos`, abre o recarga `/accesorios` y `/computadoras`.
Comprueba precios en MXN, existencias e imágenes. Aunque las APIs devuelven rutas
que comienzan con `/public/images/`, el frontend las convierte a `/images/`, que
es la ruta usada por Flask local y por el CDN de Vercel.

El cliente HTTP espera hasta 8 segundos por operación de conexión/lectura, sin
reintentos automáticos. Valida el JSON y los campos antes de mostrar tarjetas.
Si falta la URL, falla la conexión o llega una respuesta inválida, la página
muestra un aviso y un enlace para volver a intentar (estado HTTP 503).
Una lista vacía válida muestra que todavía no hay productos (HTTP 200).
Nunca se sustituyen los errores por productos de demostración.
Imágenes ausentes o rutas ajenas al directorio local usan «Imagen pendiente».

Uvicorn debe seguir ejecutándose en EC2. Su IP pública puede cambiar al detener
y arrancar la instancia: actualiza la variable y reinicia Flask si eso sucede.
El acceso a los puertos 8000 y 5000 debe permitir la IP pública desde la que se
ejecuta Flask. Una conexión rechazada o agotada requiere comprobar el proceso,
la dirección y la conectividad;
por sí sola no identifica la causa. Esta integración no cambia reglas de AWS.
Un futuro despliegue tendrá otro origen de red y requerirá configurar su acceso.

## Pruebas sin AWS

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Las pruebas simulan las respuestas de la API; no modifican AWS, RDS ni las APIs.
No sustituyen la prueba de conectividad real descrita arriba.
El diseño CSS y el JavaScript existentes se conservan. En esta versión del
repositorio no hay controles de búsqueda ni filtros de catálogo implementados.
