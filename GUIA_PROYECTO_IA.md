# Guía de contexto del proyecto Quirón

Este documento describe el estado del repositorio para que una persona o
asistente de programación pueda entender el propósito, la arquitectura, las
reglas de datos y la forma de ejecutar y probar el proyecto antes de proponer
cambios.

## 1. Resumen

**Quirón** es un dashboard web académico para explorar y visualizar la oferta
registrada de servicios quirúrgicos de las Instituciones Prestadoras de
Servicios de Salud (IPS) de Bogotá D.C. Fue desarrollado como proyecto de
grado para la Fundación Universitaria Compensar.

La aplicación permite:

- Consultar indicadores agregados de sedes, servicios y naturaleza del
  prestador.
- Filtrar la oferta por código de servicio, naturaleza, tipo de prestador y
  nombre de sede.
- Explorar en un mapa las sedes con coordenadas válidas.
- Descargar el detalle filtrado, resúmenes y metadata de trazabilidad en CSV.
- Pedir al asistente de texto/voz que cambie filtros, busque o enfoque una
  sede, limpie filtros o descargue el detalle.

No es un sistema de disponibilidad en tiempo real ni un sistema clínico. La
fuente describe oferta registrada; no permite inferir capacidad efectiva,
demanda, tiempos de espera, procedimientos realizados, resultados clínicos ni
calidad del servicio. La aplicación no incluye autenticación para usuarios
remotos.

## 2. Tecnología y ejecución rápida

- Backend y web: Python, Dash.
- Datos y transformaciones: pandas.
- Visualizaciones: Plotly.
- Servidor de producción: Gunicorn.
- Pruebas de navegador: Playwright para Node.js.
- Asistente: API de Gemini, opcional.
- Mapa: teselas externas de CARTO.
- Geocodificación preprocesada: OpenStreetMap Nominatim.

Desde la raíz del repositorio:

```bash
pip install -r requirements.txt
python run.py
```

La aplicación local escucha en `http://localhost:8050`. `run.py` usa la
variable `PORT` cuando existe y tiene `8050` como valor local predeterminado.
El entrypoint WSGI para Gunicorn es `run:server`.

## 3. Mapa del repositorio

```text
run.py                         Entrypoint local y objeto WSGI para Gunicorn
requirements.txt               Dependencias Python de ejecución
runtime.txt                    Versión de Python indicada: 3.11
package.json                   Scripts y dependencias de Playwright
playwright.config.js           Configuración de E2E y servidores de prueba
quiron/
  server.py                    Carga datos y construye la aplicación Dash
  layout.py                    Estructura visual y controles
  callbacks.py                 Interacciones, filtros y descargas
  filtros.py                   Reglas de filtrado y opciones válidas
  data/
    loader.py                  Lectura, validación y unión de datos
    metrics.py                 Indicadores y resúmenes
    raw/                       CSV originales
    processed/                 CSV geocodificado utilizado por el dashboard
  visualizaciones/mapa.py      Figura Plotly del mapa de sedes
  exportacion.py               Preparación y serialización de CSV
  metadata.py                  Fuente, corte y trazabilidad
  asistente.py                 Gemini y validación de acciones permitidas
  geocoding/                   Normalización y cliente de Nominatim
  assets/
    styles.css                 Estilos del dashboard
    asistente-voz.js           Dictado, síntesis de voz e interfaz de voz
    mapa-tooltip.js            Comportamiento visual auxiliar del mapa
tests/
  test_*.py                    Pruebas unitarias de Python
  e2e/*.spec.js                Pruebas de navegador Playwright
  e2e/support/                 Servidor Gemini simulado y evidencia E2E
scripts/
  enriquecer_coordenadas.py    Proceso offline para enriquecer coordenadas
```

`app/dashboard.py` y `assets/estilos.css` son restos de una implementación
anterior. No son el entrypoint de la aplicación actual. El flujo activo es
`run.py` → `quiron.server.create_app()`.

## 4. Flujo de datos y reglas analíticas

1. `quiron.server.create_app()` llama a
   `quiron.data.loader.cargar_oferta_con_coordenadas()`.
2. El loader lee los archivos desde rutas relativas al paquete, no desde el
   directorio actual del proceso:
   - `quiron/data/raw/cirugia-plastica-01_07_2026.csv`: oferta y atributos de
     prestadores.
   - `quiron/data/processed/sedes_geocodificadas.csv`: resultados de
     geocodificación asociados por `sede_id`.
3. La fuente principal se transforma de formato ancho a largo: una fila por
   combinación de sede y servicio. Los identificadores se conservan como
   texto.
4. Los códigos quirúrgicos del alcance son `213` y `369`. Las funciones
   analíticas y de filtros aplican esta restricción.
5. Se une la información geográfica sin descartar sedes no geocodificadas.
   Solo los registros con coordenadas presentes, dentro de rango y marcadas
   como geocodificadas son válidos para el mapa.
6. Se calculan indicadores y metadata iniciales, se compone el layout y se
   registran callbacks. Los datos se cargan al arrancar y se reutilizan en
   memoria durante las interacciones.

Los archivos `osb_tipoprestadores.csv` y `osb_ofertasrv-ips-urgencias.csv`
también están disponibles en `quiron/data/raw/` y tienen funciones de carga,
pero el flujo principal actual del dashboard usa la fuente de oferta
quirúrgica y el CSV geocodificado.

### Reglas importantes

- Una sede puede aparecer varias veces porque puede ofrecer más de un
  servicio. Para indicadores de sedes se cuenta `sede_id` único, no filas.
- En `filtros.py`, los criterios distintos se combinan con AND; dentro de las
  selecciones múltiples de un mismo filtro se aceptan los valores elegidos.
- La búsqueda por nombre ignora diferencias de mayúsculas, tildes y espacios
  repetidos; no altera los nombres mostrados.
- No agregar filtros geográficos (por ejemplo, localidad o subred) sin que
  esos campos existan y estén validados en los datos.
- La cobertura geográfica no debe ocultar sedes no geocodificadas del análisis:
  estas solo se excluyen de la visualización del mapa.
- CSV de salida incluye BOM UTF-8, no incluye índice, y los nombres usan la
  hora de `America/Bogota`.

## 5. Módulos de la aplicación

- `quiron/server.py`: orquesta carga, indicadores, mapa, metadata, layout y
  callbacks.
- `quiron/data/loader.py`: lee CSV, valida columnas y existencia, transforma
  servicios, normaliza coordenadas y verifica duplicados/rangos.
- `quiron/data/metrics.py`: calcula conteos generales, por servicio y por
  naturaleza.
- `quiron/filtros.py`: crea opciones y aplica filtros a copias de la tabla.
- `quiron/layout.py`: define la interfaz Dash y los identificadores usados por
  callbacks.
- `quiron/callbacks.py`: conecta controles con métricas, mapa, tablas,
  asistente y descargas.
- `quiron/visualizaciones/mapa.py`: consolida servicios a una fila por sede y
  genera mapa interactivo; no inventa posiciones para sedes sin coordenadas.
- `quiron/exportacion.py`: prepara detalle y resúmenes, genera CSV y nombres
  de archivo.
- `quiron/metadata.py`: documenta la entidad y fuente, fecha de corte,
  cobertura y advertencias; algunos valores se calculan con la tabla cargada.
- `quiron/geocoding/normalizador.py`: expande nomenclatura abreviada de
  direcciones y elimina detalles de unidades internas que no ayudan a
  geocodificar.
- `quiron/geocoding/cliente.py`: cliente offline de Nominatim con User-Agent,
  caché y límite de velocidad. No es necesario para iniciar el dashboard,
  porque se consume el CSV de coordenadas ya procesado.
- `quiron/assets/asistente-voz.js`: usa las APIs de voz del navegador; el
  dictado se hace en el navegador y la lectura usa `speechSynthesis`.

## 6. Asistente de texto y voz

El asistente no ejecuta código arbitrario ni modifica directamente el
navegador. `quiron.asistente` pide a Gemini que devuelva un JSON con acciones
concretas; luego valida el esquema y restringe los filtros a opciones que
realmente existen en el dashboard. Valores inventados se rechazan.

Algunas acciones locales —como una solicitud explícita de descargar el detalle
filtrado o la búsqueda de una sede identificable— pueden resolverse sin pedir
una interpretación de Gemini. La solicitud de voz se transcribe en el
navegador; al servidor se envía texto, no audio.

Configuración opcional:

```text
GEMINI_API_KEY=<clave privada>
GEMINI_MODEL=gemini-3.1-flash-lite
```

El modelo es opcional y tiene un valor predeterminado en el código. En local se
puede guardar la clave en `.env` (no subirlo al repositorio); en Render se debe
configurar como variable de entorno del servicio. Nunca escribir claves reales
en código, documentación, pruebas, capturas o commits. Las pruebas E2E
normales usan un endpoint Gemini simulado local y una clave ficticia.

## 7. Pruebas

Hay pruebas unitarias Python y pruebas de extremo a extremo en navegador.

### 7.1 Pruebas unitarias Python

`pytest` no está incluido en `requirements.txt`; instalarlo en el entorno de
desarrollo si hace falta:

```bash
python -m pip install pytest
python -m pytest
```

Suites:

- `tests/test_filtros.py`: opciones, filtros, normalización de texto y conteo
  de sedes.
- `tests/test_exportacion.py`: detalle, deduplicación, resúmenes, CSV y
  nombres de exportación.
- `tests/test_metadata.py`: metadata estática/dinámica, fuente y cobertura.
- `tests/test_asistente.py`: validación de comandos, valores permitidos,
  respuestas simuladas, falta de clave y errores/cuota/tiempos de espera.
- `tests/test_normalizador.py`: normalización de direcciones bogotanas con
  casos tomados de datos reales y entradas vacías.

Ejecutar una suite concreta:

```bash
python -m pytest tests/test_filtros.py
```

### 7.2 Pruebas E2E Playwright

Instalar dependencias de Node desde la raíz:

```bash
npm install
```

Ejecutar todas las pruebas configuradas:

```bash
npm run test:e2e
```

La configuración está en `playwright.config.js`. Por defecto Playwright
arranca un mock local de Gemini y la app en el puerto `8052`; no usa una clave
real ni consume cuota de Google. Las pruebas cubren:

1. Carga inicial del dashboard.
2. Filtrar y restablecer resultados.
3. Búsqueda sin coincidencias y recuperación.
4. Descarga del detalle filtrado.
5. Descarga del resumen por servicio.
6. Descarga del resumen por naturaleza.
7. Descarga de metadata y trazabilidad.
8. Descarga local desde el asistente.
9. Solicitud de texto procesada por Gemini simulado.
10. Dictado y respuesta hablada simulados en el navegador.
11. Integración con Gemini real (opcional).

La prueba 11 se omite normalmente. Para ejecutarla desde PowerShell:

```powershell
$env:E2E_LIVE_GEMINI = "1"
npm run test:e2e
Remove-Item Env:E2E_LIVE_GEMINI
```

Esta prueba usa las credenciales configuradas en `.env` y puede consumir cuota.
En ese modo la app usa el puerto `8053`. Ejecutarla solo cuando sea necesario y
con una clave válida.

Requisitos del navegador:

- Windows: Microsoft Edge instalado; Playwright usa el canal `msedge`.
- Otros sistemas: instalar Chromium con `npx playwright install chromium`.
- Las pruebas esperan la carga del mapa y teselas externas de CARTO. Una falla
  de red externa puede afectar la prueba aunque la lógica Python funcione.
- Las pruebas de voz pueden necesitar FFmpeg en `PATH` y una voz española del
  sistema operativo para generar el video con narración.

Los informes, capturas, videos y PDFs funcionales se generan bajo
`reportes/pruebas_funcionales/` y son artefactos de prueba, no fuentes de datos.

## 8. Despliegue en Render

Crear un **Web Service** conectado al repositorio y elegir la rama que contiene
los archivos que se desean publicar. Si el repositorio conectado tiene la
aplicación en su raíz, dejar **Root Directory** vacío. Si se conectó un
monorepo que contiene `Proyecto-fin-de-grado/`, establecer esa carpeta como
Root Directory.

Valores recomendados:

| Opción | Valor |
|---|---|
| Language | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn run:server --bind 0.0.0.0:$PORT --workers 1 --timeout 120` |
| Python | 3.11 |

`runtime.txt` fija actualmente Python 3.11. `pandas==2.2.2` está fijado en
`requirements.txt`; no desplegar este conjunto como Python 3.14, porque pip
puede intentar compilar pandas desde código fuente y fallar. Si Render no
respeta `runtime.txt`, fijar `PYTHON_VERSION` a una versión 3.11 disponible en
la configuración del servicio (por ejemplo `3.11.11`) y revisar en el log que
la instalación realmente se ejecute bajo Python 3.11.

Si se habilita el asistente en producción, añadir `GEMINI_API_KEY` en la
configuración de variables de entorno de Render. No poner la clave en el
Start Command ni en el repositorio. La app no incluye autenticación: si se
publica, será accesible desde Internet. El plan gratuito puede suspender
servicios inactivos y tiene recursos limitados; la app necesita los CSV
versionados del repositorio en cada despliegue.

## 9. Datos, trazabilidad y límites conocidos

- La metadata fija el corte declarado en `2026-07-01`, derivado del nombre de
  la fuente principal. El propio código advierte que debe verificarse contra
  la documentación oficial del recurso antes de una entrega definitiva.
- La fuente referenciada es Datos Abiertos Bogotá / Secretaría Distrital de
  Salud. Su URL y la advertencia metodológica están en `quiron/metadata.py`.
- Los resultados son oferta registrada y no disponibilidad actual.
- Coordenadas procesadas pueden ser incompletas; sedes sin coordenadas siguen
  disponibles en filtros e indicadores, pero no aparecen en el mapa.
- Mapa base y servicios de voz/Gemini pueden depender de red, navegador,
  permisos o cuotas externas.
- `quiron/geocoding/cliente.py` consulta Nominatim y guarda una caché local
  bajo `quiron/data/cache/`; respetar el límite de solicitudes y la política de
  uso si se vuelve a ejecutar el proceso offline.

## 10. Guía para cambios futuros

1. Antes de cambiar una regla analítica, revisar `loader.py`, `filtros.py`,
   `metrics.py`, `callbacks.py` y las pruebas correspondientes.
2. Mantener los conteos de sedes basados en `sede_id` único, excepto cuando
   explícitamente se mida el número de registros sede-servicio.
3. No presentar datos inferidos como datos de la fuente. Conservar registros
   sin coordenadas y expresar ausencias explícitamente.
4. Si cambian fuentes o el periodo, actualizar validaciones, fecha y
   advertencias en `metadata.py`, la documentación y pruebas de datos.
5. Si cambia el comando estructurado del asistente, mantener el esquema,
   validación allowlist y pruebas para rechazar opciones no existentes.
6. Si se modifica la interfaz o sus identificadores, actualizar las
   expectativas Playwright afectadas.
7. No incluir `.env`, credenciales, cachés, perfiles ni reportes locales en
   commits.
8. Ejecutar al menos las pruebas unitarias relacionadas; para cambios de UI,
   callbacks, descarga o asistente, ejecutar también las E2E pertinentes.

## 11. Referencias principales

- `README.md`: instrucciones originales de ejecución, asistente y Playwright.
- `run.py`: entrypoint que Render/Gunicorn debe cargar.
- `quiron/server.py`: creación de la aplicación.
- `quiron/metadata.py`: fuente y definiciones metodológicas.
- `requirements.txt`, `runtime.txt`, `package.json` y
  `playwright.config.js`: dependencias y configuración de ejecución/pruebas.
