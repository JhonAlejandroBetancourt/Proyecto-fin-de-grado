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