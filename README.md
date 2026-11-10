# Quirón

Radar de oferta quirúrgica de las IPS de Bogotá D.C. — proyecto de grado,
Fundación Universitaria Compensar.

## Uso local

pip install -r requirements.txt
python run.py

Abre http://localhost:8050

## Dashboard y área de proceso ETL

El dashboard y el área **Proceso ETL** se navegan por separado desde el menú
principal (`/` y `/etl`). Esta última permite subir un archivo CSV compatible
y revisar el estado de la carga, los errores, el historial de ejecuciones y
la trazabilidad del mapeo de campos. La administración de usuarios también
se encuentra en su ruta independiente (`/admin`).

La carga acepta un único archivo `.csv` de hasta 10 MB. Debe conservar la
estructura de la fuente oficial: separador `;`, codificación UTF-8 y
columnas de sede, dirección, contacto, naturaleza, tipo de prestador y
servicios codificados. Si la lectura o validación falla, el dashboard
mantiene el último conjunto de datos válido. Una carga correcta actualiza
los indicadores, filtros, mapa, tablas y exportaciones; el archivo cargado
permanece solo en el estado de la sesión del navegador y no se guarda en el
servidor. El historial y los datos procesados se conservan al navegar entre
el dashboard y ETL dentro de la misma sesión, pero no se persisten al cerrar
o recargar la pestaña.

Las coordenadas se asocian mediante una coincidencia única del nombre de la
sede y su dirección normalizados, no por el orden de las filas ni por la
huella binaria completa del archivo. Así, volver a guardar o reordenar un CSV
no elimina coordenadas válidas, y las sedes ambiguas o sin coincidencia se
mantienen sin ubicación para evitar asignaciones incorrectas.

## Acceso de usuarios y administración

La aplicación integra Supabase Auth para correo/contraseña, MFA TOTP y SSO
con Google. Las rutas Dash, sus callbacks y el panel `/admin` quedan
protegidos cuando la autenticación está activada. La sesión de aplicación se
mantiene en una cookie `HttpOnly`, `SameSite=Lax` y, bajo HTTPS, `Secure`;
los JWT se validan con las claves públicas JWKS de Supabase. Se requiere MFA
de nivel `aal2` para todas las cuentas. El navegador mantiene la sesión de
Supabase en el almacenamiento de la pestaña y renueva la cookie `HttpOnly`
al refrescarse el token; al volver a una pestaña con la cookie vencida,
intenta renovar la sesión antes de cargar el dashboard.

Para desarrollo local, copia `.env.example` a `.env` y deja
`QUIRON_AUTH_ENABLED=0`. En Vercel, la autenticación se activa por defecto y
la aplicación falla al arrancar si falta su configuración; no publiques la
rama de autenticación hasta cargar estas variables en las opciones de
entorno de Vercel:

- `SUPABASE_URL` y `SUPABASE_ANON_KEY` del proyecto. La clave puede ser la
  publishable `sb_publishable_...` o la heredada `anon`.
- `SUPABASE_SERVICE_ROLE_KEY`, solo del lado servidor. Puedes usar la nueva
  clave `sb_secret_...` o la heredada `service_role`; nunca la expongas al
  navegador ni la guardes en el repositorio.
- `QUIRON_BASE_URL`, el origen público exacto, por ejemplo
  `https://tu-dominio.vercel.app`.
- `QUIRON_ADMIN_EMAILS`, lista separada por comas con las cuentas
  administradoras iniciales.
- `QUIRON_GOOGLE_ALLOWED_EMAILS`, lista de correos autorizados para Google.
  Déjala vacía para desactivar ese botón.

En Supabase configura Google como proveedor, registra la URL de Quirón en
las redirecciones permitidas, desactiva el registro público y crea o invita
solamente cuentas autorizadas. Crea primero la cuenta administradora inicial
en Supabase e incluye su correo tanto en `QUIRON_ADMIN_EMAILS` como en
`QUIRON_GOOGLE_ALLOWED_EMAILS` si usará Google. Las cuentas invitadas desde
`/admin` reciben un enlace para establecer su contraseña y deben registrar
una aplicación TOTP en su primer acceso. Una cuenta Google también debe estar
autorizada por correo; el rol de administrador inicial se toma de
`QUIRON_ADMIN_EMAILS`.

El panel `/admin` permite invitar usuarios, ver el último inicio de sesión,
enviar enlaces de restablecimiento de contraseña y eliminar cuentas no
administradoras. La clave `SUPABASE_SERVICE_ROLE_KEY` se utiliza únicamente
para operaciones administrativas y no debe compartirse por chat, incluirse
en capturas o enviarse al navegador. Configura todos los valores en Vercel
antes de integrar la rama en `main`. El navegador usa el cliente oficial
Supabase JS, fijado a una versión e integrity hash; la cookie de acceso es
`HttpOnly`, y el SDK conserva la sesión de renovación solo en el
`sessionStorage` de esa pestaña.

Las claves modernas `sb_publishable_...` y `sb_secret_...` se envían solo en
el encabezado `apikey`, como requiere Supabase. Las claves heredadas `anon` y
`service_role` también se envían como `Authorization: Bearer`.

## Pruebas unitarias y cobertura

Las pruebas unitarias cubren las capas de datos, filtros, metadata,
exportación, asistente y normalización. Desde la raíz del proyecto:

```powershell
pip install -r requirements.txt
pytest
```

Para medir la cobertura de código del paquete `quiron`:

```powershell
pytest --cov=quiron
```

Añade `--cov-report=html` para generar un informe navegable en `htmlcov/`
(carpeta excluida de Git). La configuración de `pytest` y `coverage` vive en
`pyproject.toml`.

## Asistente de voz con Gemini

El asistente acepta solicitudes escritas o dictadas para aplicar los filtros
disponibles, buscar una sede, centrar el mapa en una sede georreferenciada o
descargar el detalle CSV de los resultados filtrados.
La orden explícita de descargar el detalle filtrado se ejecuta localmente y
descarga el mismo CSV que el botón de exportación. El dictado se transcribe en
el navegador y a Gemini solo se le envía texto;
la respuesta aparece en pantalla y el navegador la lee en voz alta. Las
órdenes que mencionen el nombre completo de una sede georreferenciada para
mostrarla en el mapa se resuelven localmente, sin llamar a Gemini.
Para las demás solicitudes, Gemini interpreta texto y solo puede elegir entre
acciones y valores que ya existen en el dashboard; no recibe acceso arbitrario
al navegador.

1. Crea una clave de Gemini en [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Copia `.env.example` a `.env` y define `GEMINI_API_KEY` con tu clave.
3. Opcionalmente, cambia `GEMINI_MODEL` en `.env`; por defecto se usa
   `gemini-3.1-flash-lite`, configurado con esfuerzo de razonamiento bajo para
   mantener ágiles las solicitudes de filtros.
4. Reinicia `python run.py` y abre la aplicación en Chrome o Edge.
5. Pulsa **Hablar** y concede permiso al micrófono, o escribe una solicitud y
   pulsa **Enviar**.

La clave solo se lee en el servidor y `.env` está excluido de Git. Gemini
recibe el texto de la solicitud, no el audio. El dictado usa el reconocimiento
de voz del navegador y puede requerir una conexión a Internet y sus propios
permisos; el proveedor del navegador puede procesar el audio. Si el navegador
no lo admite, puedes escribir la solicitud. El micrófono permanece en escucha
continua hasta que pulses **Detener**; la transcripción completa se envía
entonces como texto. La lectura en voz alta usa `speechSynthesis` y depende de
las voces disponibles en el sistema.

La API de Gemini puede tener límites o costes según la cuenta y el uso.
Si se agota la cuota, el asistente mostrará el tiempo de renovación que
informe Google; puedes revisar los límites y la facturación en Google AI Studio.
Configura límites y autenticación antes de publicar la aplicación en Internet;
este asistente no incluye control de acceso para usuarios remotos.

## Pruebas funcionales con Playwright

Las pruebas de navegador recorren la plataforma como una persona usuaria:
carga del dashboard, filtros, limpieza, asistente de texto/voz y descarga de
los cuatro CSV. La prueba de filtros compara numéricamente los indicadores
generales y geográficos antes y después de seleccionar un servicio, comprueba
su restablecimiento y adjunta capturas separadas de ambos estados.

Desde la raíz del proyecto, instala las dependencias de pruebas:

```powershell
npm install
```

Ejecuta los escenarios:

```powershell
npm run test:e2e
```

Playwright inicia automáticamente la aplicación en un puerto aislado
(`http://127.0.0.1:8052`) y un endpoint Gemini simulado local para comprobar
el viaje petición-respuesta sin enviar solicitudes ni credenciales a Google.
Cada escenario crea un PDF independiente y capturas PNG en
`reportes/pruebas_funcionales/`; los círculos rojos numerados señalan los
controles pulsados durante la prueba. En Windows se requiere Microsoft Edge
instalado; en otros sistemas, instala Chromium con
`npx playwright install chromium`. Todos los escenarios esperan que Plotly,
el estilo, el lienzo y el mapa hayan terminado de cargar. Si el mapa no queda
listo, la prueba falla con diagnóstico en lugar de generar una captura blanca.
El mapa base utiliza teselas de CARTO, por lo que depende de ese servicio
externo.

Las pruebas de voz comprueban que speechSynthesis recibe la respuesta en
`es-CO` y generan un MP4 con fotogramas de los pasos y narración audible en
español en `reportes/pruebas_funcionales/`. En Windows se requiere FFmpeg
accesible en PATH y una voz española de Windows instalada. El MP4 narra el
mismo texto devuelto por la plataforma.

La prueba opcional con Gemini real consume cuota y necesita una clave válida
en `.env`. En PowerShell:

```powershell
$env:E2E_LIVE_GEMINI = "1"
npm run test:e2e
Remove-Item Env:E2E_LIVE_GEMINI
```

Este modo inicia otra instancia aislada en el puerto `8053` y envía únicamente
la solicitud de prueba «filtra las sedes públicas» al servicio configurado.