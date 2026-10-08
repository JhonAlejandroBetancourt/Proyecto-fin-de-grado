# Quirón

Radar de oferta quirúrgica de las IPS de Bogotá D.C. — proyecto de grado,
Fundación Universitaria Compensar.

## Uso local

pip install -r requirements.txt
python run.py

Abre http://localhost:8050

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