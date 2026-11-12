# Guía Completa del Proyecto Quirón

## Documentación Técnica para Trabajo de Grado

**Título del Proyecto:** Dashboard para el análisis de la oferta registrada de servicios quirúrgicos de las IPS de Bogotá D.C.

**Institución:** Fundación Universitaria Compensar

**Fecha de Documentación:** Noviembre 2026

> **Nota para asistentes de IA:** Este documento es la fuente de verdad técnica
> del proyecto Quirón. Está pensado para que una IA pueda leerlo y, a partir de
> él, redactar o actualizar la documentación formal del trabajo de grado
> (documento Word) con precisión. Cada sección incluye nombres reales de
> archivos, módulos, rutas, identificadores y cifras verificadas contra el
> código fuente. Las secciones 12 (Proceso ETL Observable) y 13 (Autenticación
> y Administración) describen las funcionalidades más recientes del sistema.

---

## Índice de Contenidos

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Descripción del Problema y Justificación](#2-descripción-del-problema-y-justificación)
3. [Objetivos del Proyecto](#3-objetivos-del-proyecto)
4. [Arquitectura del Sistema](#4-arquitectura-del-sistema)
5. [Tecnologías Utilizadas](#5-tecnologías-utilizadas)
6. [Estructura del Código Fuente](#6-estructura-del-código-fuente)
7. [Descripción de la Interfaz Visual](#7-descripción-de-la-interfaz-visual)
8. [Funcionalidades del Sistema](#8-funcionalidades-del-sistema)
9. [Flujo de Datos y Procesamiento](#9-flujo-de-datos-y-procesamiento)
10. [Asistente de Voz e Inteligencia Artificial](#10-asistente-de-voz-e-inteligencia-artificial)
11. [Sistema de Exportación de Datos](#11-sistema-de-exportación-de-datos)
12. [Proceso ETL Observable](#12-proceso-etl-observable)
13. [Autenticación y Administración de Usuarios](#13-autenticación-y-administración-de-usuarios)
14. [Pruebas y Validación](#14-pruebas-y-validación)
15. [Despliegue y Configuración](#15-despliegue-y-configuración)
16. [Limitaciones y Alcance](#16-limitaciones-y-alcance)
17. [Glosario Técnico](#17-glosario-técnico)
18. [Referencias](#18-referencias)

---

## 1. Resumen Ejecutivo

### 1.1 ¿Qué es Quirón?

**Quirón** es un dashboard web interactivo diseñado para explorar y visualizar la oferta registrada de servicios quirúrgicos de las Instituciones Prestadoras de Servicios de Salud (IPS) en Bogotá D.C. El nombre hace referencia a Quirón, el centauro de la mitología griega conocido por su sabiduría en medicina y artes curativas.

### 1.2 Propósito Principal

El sistema permite a investigadores, estudiantes, profesionales de la salud y ciudadanos interesados:

- **Consultar indicadores agregados** de sedes, servicios quirúrgicos y naturaleza de los prestadores.
- **Filtrar dinámicamente** la información por múltiples criterios.
- **Visualizar geográficamente** la distribución de las IPS con oferta quirúrgica.
- **Descargar datos** en formato CSV para análisis externos.
- **Interactuar mediante voz** con un asistente inteligente basado en Gemini.
- **Cargar un CSV propio y observar el proceso ETL completo** (extracción, limpieza, transformación, validación y carga) con histórico de ejecuciones, trazas de mapeo de campos, métricas por etapa y errores visibles, en un área dedicada (`/etl`).
- **Autenticarse de forma segura** mediante Supabase Auth (correo/contraseña con MFA TOTP obligatorio y SSO con Google) y **administrar usuarios** desde un panel dedicado (`/admin`).

### 1.2.1 Evolución del Sistema

El sistema evolucionó de un dashboard de página única a una **aplicación multipágina** con tres áreas navegables desde el menú principal:

| Ruta | Área | Contenido |
|------|------|-----------|
| `/` | Dashboard | Indicadores, filtros, mapa, tablas, exportación y asistente |
| `/etl` | Proceso ETL | Carga de CSV, historial de ejecuciones, traza de mapeo, errores |
| `/admin` | Administración | Gestión de usuarios (invitar, restablecer contraseña, eliminar) |
| `/login` y `/logout` | Sesión | Inicio y cierre de sesión con Supabase Auth |

### 1.3 Contexto Académico

Este proyecto fue desarrollado como trabajo de grado para la **Fundación Universitaria Compensar**, aplicando conocimientos de desarrollo web, ciencia de datos, visualización de información e integración de inteligencia artificial.

### 1.4 Alcance y Limitaciones

> ⚠️ **Importante:** Quirón **NO** es un sistema clínico ni de disponibilidad en tiempo real. Los datos representan la **oferta registrada** en fuentes oficiales y no permiten inferir:
> - Capacidad efectiva de atención
> - Disponibilidad de citas o procedimientos
> - Tiempos de espera
> - Demanda real de servicios
> - Resultados clínicos o calidad del servicio

---

## 2. Descripción del Problema y Justificación

### 2.1 Problemática Identificada

En Colombia, y específicamente en Bogotá D.C., existe una necesidad creciente de herramientas que faciliten el acceso y análisis de información sobre la oferta de servicios de salud. Los datos sobre IPS habilitadas están disponibles en portales de datos abiertos, pero su formato crudo dificulta:

- La consulta rápida y eficiente por parte de ciudadanos
- El análisis geográfico de la distribución de servicios
- La comparación entre diferentes tipos de prestadores
- La toma de decisiones informadas sobre dónde buscar atención

### 2.2 Justificación del Proyecto

Este proyecto aborda la necesidad de:

1. **Democratizar el acceso a la información:** Transformar datos públicos en visualizaciones comprensibles.
2. **Facilitar la exploración interactiva:** Permitir filtrado dinámico sin conocimientos técnicos.
3. **Incorporar tecnologías modernas:** Integrar asistentes de voz con IA para una experiencia más accesible.
4. **Garantizar trazabilidad:** Documentar fuentes y limitaciones metodológicas.

### 2.3 Fuente de Datos

| Atributo | Valor |
|----------|-------|
| **Entidad publicadora** | Secretaría Distrital de Salud de Bogotá |
| **Portal** | Datos Abiertos Bogotá |
| **Conjunto de datos** | IPS habilitadas con oferta de servicios quirúrgicos de cirugía estética |
| **URL oficial** | https://datosabiertos.bogota.gov.co/dataset/ips-servicios-cirugia-estetica |
| **Fecha de corte** | 01/07/2026 |
| **Cobertura geográfica** | Bogotá D.C. |

---

## 3. Objetivos del Proyecto

### 3.1 Objetivo General

Desarrollar un dashboard web interactivo que permita consultar, filtrar, visualizar y exportar la oferta registrada de servicios quirúrgicos de las IPS de Bogotá D.C., integrando un asistente de voz basado en inteligencia artificial.

### 3.2 Objetivos Específicos

1. **Diseñar e implementar** una interfaz de usuario intuitiva y accesible.
2. **Desarrollar un sistema de filtrado** dinámico por múltiples criterios.
3. **Crear visualizaciones geográficas** interactivas con mapas.
4. **Implementar exportación de datos** en formato CSV con trazabilidad.
5. **Integrar un asistente de voz** que interprete comandos en lenguaje natural.
6. **Implementar un proceso ETL observable** que permita cargar fuentes CSV y auditar cada etapa (extracción, limpieza, transformación, validación y carga) con métricas, historial y traza de mapeo de campos.
7. **Incorporar autenticación y control de acceso** con MFA y administración de usuarios para el despliegue en producción.
8. **Documentar metodológicamente** las fuentes y limitaciones del análisis.
9. **Garantizar la calidad** mediante pruebas automatizadas unitarias, de integración y de navegador.

---

## 4. Arquitectura del Sistema

### 4.1 Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLIENTE (Navegador)                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │   Interfaz  │  │    Mapa     │  │  Controles  │  │   Asistente    │ │
│  │    Dash     │  │   Plotly    │  │  de Filtro  │  │   de Voz       │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └────────┬───────┘ │
│         │                │                │                   │         │
│         └────────────────┴────────────────┴───────────────────┘         │
│                                   │                                      │
│                          Callbacks Dash                                  │
└───────────────────────────────────┼─────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                           SERVIDOR (Python/Dash)                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌─────────────────────┐ │
│  │  server.py │  │ callbacks  │  │  filtros   │  │     asistente       │ │
│  │ (arranque) │  │   .py      │  │    .py     │  │       .py           │ │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └──────────┬──────────┘ │
│        │               │               │                    │            │
│        ▼               ▼               ▼                    ▼            │
│  ┌─────────────────────────────────────────────┐   ┌─────────────────┐  │
│  │               DATA LAYER                     │   │   API Gemini    │  │
│  │  loader.py │ metrics.py │ exportacion.py    │   │   (Externo)     │  │
│  └──────────────────┬──────────────────────────┘   └─────────────────┘  │
│                     │                                                    │
│                     ▼                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                         ARCHIVOS CSV                                 ││
│  │  raw/cirugia-plastica.csv  │  processed/sedes_geocodificadas.csv   ││
│  └─────────────────────────────────────────────────────────────────────┘│
└───────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                        SERVICIOS EXTERNOS                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐   │
│  │  Teselas CARTO  │  │  OpenStreetMap  │  │     Google Gemini       │   │
│  │   (Mapa base)   │  │   (Nominatim)   │  │   (Interpretación IA)   │   │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────┘   │
└───────────────────────────────────────────────────────────────────────────┘
```

> **Nota:** Además de lo representado, el sistema incorpora dos capas transversales no mostradas en el diagrama: la **capa ETL observable** (`quiron/etl/`) entre la carga de archivos y el DATA LAYER, y la **capa de autenticación** (`quiron/auth.py` + Supabase Auth como servicio externo) que protege todas las rutas en producción. Ambas se detallan en las secciones 12 y 13.

### 4.2 Patrón de Diseño

El proyecto sigue una arquitectura **MVC adaptada para Dash**, ampliada con capas transversales de ETL y seguridad:

- **Modelo (Model):** `loader.py`, `metrics.py`, `filtros.py` - Gestión de datos.
- **Vista (View):** `layout.py`, `assets/`, `templates/` - Definición de la interfaz (dashboard multipágina y páginas de sesión/administración).
- **Controlador (Controller):** `callbacks.py`, `asistente.py` - Lógica de interacción.
- **Capa ETL (Pipeline):** `etl/pipeline.py`, `etl/observabilidad.py` - Orquestación instrumentada del proceso de datos con trazabilidad completa.
- **Capa de Seguridad:** `auth.py` - Autenticación con Supabase, protección de rutas, cabeceras de seguridad y API administrativa.

### 4.2.1 Arquitectura Multipágina

El enrutamiento se hace con `dcc.Location` dentro de una única aplicación Dash. Las tres páginas (`#dashboard-page`, `#etl-page`, `#admin` vía Flask) comparten los `dcc.Store` de sesión, de modo que el dataset activo y el historial ETL se conservan al navegar entre dashboard y ETL dentro de la misma pestaña:

| Store | Contenido | Persistencia |
|-------|-----------|--------------|
| `etl-dataset-activo` | Tabla resultante del último ETL válido (serializada) | Sesión de la pestaña |
| `etl-traza` | Traza completa: pasos, mapeos, errores, historial acumulado, número de ejecución | Sesión de la pestaña |

### 4.3 Flujo de Arranque

```
1. run.py
   └── 2. quiron.server.create_app()
       ├── 3. cargar_oferta_con_coordenadas()
       │   ├── Lee CSV de oferta quirúrgica
       │   ├── Lee CSV de coordenadas geocodificadas
       │   └── Une y valida datos
       ├── 4. Calcula indicadores iniciales
       ├── 5. Genera mapa con Plotly
       ├── 6. Construye opciones de filtros
       ├── 7. Genera metadata de trazabilidad
       ├── 8. Compone layout visual
       └── 9. Registra callbacks interactivos
```

---

## 5. Tecnologías Utilizadas

### 5.1 Stack Tecnológico Principal

| Categoría | Tecnología | Versión | Propósito |
|-----------|------------|---------|-----------|
| **Backend** | Python | 3.11 | Lenguaje principal |
| **Framework Web** | Dash | 2.17.1 | Aplicación web reactiva multipágina |
| **Manipulación de Datos** | pandas | 2.2.2 | Procesamiento de CSV |
| **Visualizaciones** | Plotly | 5.24.1 | Gráficos y mapas interactivos |
| **Servidor Producción** | Gunicorn | 22.0.0 | WSGI para despliegue |
| **Validación JWT** | PyJWT[crypto] | 2.10.1 | Verificación de tokens de Supabase con JWKS |
| **Variables de entorno** | python-dotenv | 1.0.1 | Carga de configuración local |
| **Pruebas unitarias** | pytest / pytest-cov | 8.3.3 / 5.0.0 | Pruebas y cobertura |
| **Pruebas E2E** | Playwright | Node.js (@playwright/test ^1.55) | Pruebas de navegador |
| **IA/Asistente** | Google Gemini | API | Interpretación de comandos |
| **Autenticación** | Supabase Auth | API + supabase-js | Correo/contraseña, MFA TOTP, SSO Google |
| **Hosting Producción** | Vercel | - | Despliegue continuo desde GitHub |

### 5.2 Servicios Externos

| Servicio | Uso en el Proyecto |
|----------|-------------------|
| **CARTO** | Teselas del mapa base (capa cartográfica) |
| **OpenStreetMap Nominatim** | Geocodificación de direcciones (preprocesado) |
| **Google Gemini** | Interpretación de solicitudes en lenguaje natural |
| **Web Speech API** | Dictado y síntesis de voz en el navegador |
| **Supabase Auth** | Autenticación, MFA TOTP, SSO con Google y API administrativa de usuarios |
| **Vercel** | Hosting de producción con despliegue continuo por rama (`main` → producción, ramas feature → preview) |

### 5.3 Ejecución Rápida

```bash
# Clonar e instalar dependencias
pip install -r requirements.txt

# Ejecutar localmente
python run.py
# → La aplicación estará disponible en http://localhost:8050

# Ejecutar pruebas E2E
npm install
npm run test:e2e
```

---

## 6. Estructura del Código Fuente

### 6.1 Árbol de Directorios

```
Proyecto-fin-de-grado/
│
├── run.py                          # Punto de entrada (local, Gunicorn y Vercel)
├── requirements.txt                # Dependencias Python
├── runtime.txt                     # Versión de Python (3.11)
├── pyproject.toml                  # Config pytest/coverage y entrypoint Vercel
├── package.json                    # Dependencias Node/Playwright
├── playwright.config.js            # Configuración de pruebas E2E
├── .env.example                    # Plantilla de variables de entorno
│
├── quiron/                         # 📦 PAQUETE PRINCIPAL
│   ├── _init_.py                   # Inicializador del paquete
│   ├── server.py                   # Orquestador de la aplicación
│   ├── layout.py                   # Estructura visual multipágina (/, /etl)
│   ├── callbacks.py                # Lógica de interacciones y carga ETL
│   ├── auth.py                     # Autenticación Supabase, rutas protegidas, /admin API
│   ├── filtros.py                  # Sistema de filtrado
│   ├── exportacion.py              # Generación de CSV de salida
│   ├── metadata.py                 # Trazabilidad y fuente de datos
│   ├── asistente.py                # Integración con Gemini
│   ├── theme.py                    # Configuración de colores/tema
│   │
│   ├── etl/                        # ⚙️ PIPELINE ETL OBSERVABLE
│   │   ├── pipeline.py             # Orquestación instrumentada (ejecutar_etl)
│   │   └── observabilidad.py       # Modelo de trazas: PasoETL, MapeoCampo, TrazaETL
│   │
│   ├── data/                       # 📁 CAPA DE DATOS
│   │   ├── loader.py               # Carga, limpieza y validación de CSV (instrumentada)
│   │   ├── metrics.py              # Cálculo de indicadores
│   │   ├── raw/                    # Archivos CSV originales
│   │   │   ├── cirugia-plastica-01_07_2026.csv
│   │   │   ├── osb_tipoprestadores.csv
│   │   │   └── osb_ofertasrv-ips-urgencias.csv
│   │   └── processed/              # Datos preprocesados
│   │       └── sedes_geocodificadas.csv
│   │
│   ├── visualizaciones/            # 📊 VISUALIZACIONES
│   │   └── mapa.py                 # Construcción del mapa Plotly
│   │
│   ├── geocoding/                  # 🗺️ GEOCODIFICACIÓN
│   │   ├── normalizador.py         # Normalización de direcciones
│   │   └── cliente.py              # Cliente de Nominatim
│   │
│   ├── templates/                  # 🔐 PÁGINAS DE SESIÓN (Flask/Jinja)
│   │   ├── login.html              # Inicio de sesión, MFA TOTP, SSO Google
│   │   ├── logout.html             # Cierre de sesión
│   │   └── admin.html              # Panel de administración de usuarios
│   │
│   └── assets/                     # 🎨 RECURSOS FRONTEND
│       ├── styles.css              # Estilos CSS (dashboard, ETL, navegación)
│       ├── asistente-voz.js        # Lógica de voz del navegador
│       ├── auth-session.js         # Renovación de sesión y cookie HttpOnly
│       └── mapa-tooltip.js         # Comportamiento del mapa
│
├── tests/                          # 🧪 PRUEBAS
│   ├── test_filtros.py             # Pruebas de filtrado
│   ├── test_exportacion.py         # Pruebas de exportación
│   ├── test_metadata.py            # Pruebas de metadata
│   ├── test_asistente.py           # Pruebas del asistente
│   ├── test_mapa.py                # Pruebas del mapa
│   ├── test_etl.py                 # Pruebas del pipeline ETL y su traza
│   ├── test_etl_upload.py          # Integración: carga CSV vía endpoint Dash
│   ├── test_auth.py                # Pruebas de autenticación y autorización
│   ├── test_vercel_entrypoint.py   # Punto de entrada WSGI para Vercel
│   ├── test_normalizador.py        # Pruebas de normalización
│   └── e2e/                        # Pruebas de navegador
│       ├── dashboard.spec.js       # Carga del dashboard y filtros
│       ├── asistente.spec.js       # Asistente de voz
│       ├── exportaciones.spec.js   # Descargas CSV
│       ├── ai.spec.js              # Gemini simulado (mock)
│       ├── ai-live.spec.js         # Gemini real (opcional)
│       ├── etl.spec.js             # Carga CSV y trazabilidad del proceso ETL
│       └── support/                # Mock de Gemini y utilidades de evidencia
│
├── scripts/                        # 🔧 SCRIPTS AUXILIARES
│   └── enriquecer_coordenadas.py   # Proceso de geocodificación
│
└── reportes/                       # 📑 EVIDENCIAS DE PRUEBAS
    └── pruebas_funcionales/        # Capturas, PDFs y videos
```

### 6.2 Descripción de Módulos Principales

| Módulo | Responsabilidad |
|--------|-----------------|
| `server.py` | Orquesta la creación de la app Dash, carga datos, calcula indicadores y registra callbacks |
| `layout.py` | Define toda la estructura visual multipágina (dashboard y área ETL) sin lógica de datos |
| `callbacks.py` | Conecta controles con acciones: filtrado, gráficos, descargas, navegación entre páginas y carga de CSV al ETL |
| `auth.py` | Carga configuración de Supabase, protege rutas y callbacks, valida JWT (JWKS), exige MFA `aal2`, expone API `/admin` |
| `etl/pipeline.py` | Ejecuta el ETL instrumentado (`ejecutar_etl`): calcula huella SHA-256, orquesta etapas, captura errores sin interrumpir la app y serializa la traza |
| `etl/observabilidad.py` | Modelo de observabilidad: `PasoETL` (orden, fase, nivel, métricas, duración), `MapeoCampo` (origen→destino) y `TrazaETL` (acumulador serializable) |
| `filtros.py` | Implementa la lógica de filtrado y genera opciones válidas |
| `loader.py` | Lee, limpia, valida y transforma los archivos CSV fuente; cada etapa emite eventos a un observador opcional |
| `metrics.py` | Calcula conteos y estadísticas agregadas |
| `exportacion.py` | Prepara DataFrames para descarga en formato CSV |
| `metadata.py` | Centraliza información de trazabilidad y advertencias metodológicas |
| `asistente.py` | Procesa solicitudes con Gemini y valida acciones permitidas |
| `mapa.py` | Construye la figura del mapa interactivo con Plotly |

---

## 7. Descripción de la Interfaz Visual

### 7.1 Composición General de la Interfaz

La interfaz de Quirón es **multipágina**. El encabezado incluye un menú de navegación con los enlaces **Dashboard** (`/`, id `nav-dashboard`) y **Proceso ETL** (`/etl`, id `nav-etl`); el enlace activo se resalta con la clase CSS `activo`. La página del dashboard (`#dashboard-page`) está organizada en **secciones verticales** que guían al usuario desde la información general hasta los detalles:

```
┌─────────────────────────────────────────────────────────────────────┐
│  ⚕ QUIRÓN - Radar de oferta quirúrgica de las IPS de Bogotá D.C.   │
│                    Fundación Universitaria Compensar                 │
│              [ Dashboard ]  [ Proceso ETL ]   ← navegación          │
├─────────────────────────────────────────────────────────────────────┤
│                        PANEL DE INDICADORES (KPIs)                   │
│  🏥 Sedes registradas │ ⚕ Oferta quirúrgica │ ▤ Códigos │ 🏛 Públicas │
├─────────────────────────────────────────────────────────────────────┤
│                      FUENTE Y TRAZABILIDAD                          │
│  Entidad · Portal · Fecha corte · Cobertura · Advertencias          │
├─────────────────────────────────────────────────────────────────────┤
│                       EXPLORAR LA OFERTA                            │
│  [Filtro Servicio] [Filtro Naturaleza] [Filtro Tipo] [Buscar Sede]  │
├─────────────────────────────────────────────────────────────────────┤
│                       ASISTENTE DE VOZ                               │
│  [Campo de texto] [🎤 Hablar] [Enviar]  →  Respuesta del asistente  │
├─────────────────────────────────────────────────────────────────────┤
│                    DISTRIBUCIÓN GEOGRÁFICA                          │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                                                             │    │
│  │                    MAPA INTERACTIVO                         │    │
│  │                     (Plotly + CARTO)                        │    │
│  │                                                             │    │
│  └─────────────────────────────────────────────────────────────┘    │
│  Sedes visibles: XX │ Sin coordenadas: XX │ Cobertura: XX%          │
├─────────────────────────────────────────────────────────────────────┤
│                      TABLAS DESCRIPTIVAS                            │
│  ┌──────────────────────┐  ┌──────────────────────┐                │
│  │ Sedes por Servicio   │  │ Sedes por Naturaleza │                │
│  └──────────────────────┘  └──────────────────────┘                │
├─────────────────────────────────────────────────────────────────────┤
│                     DESCARGAR RESULTADOS                            │
│  [📥 Detalle] [📥 Por Servicio] [📥 Por Naturaleza] [📥 Metadata]   │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.2 Componentes Visuales Detallados

#### 7.2.1 Encabezado Institucional

- **Emblema:** Símbolo ⚕ representando el área médica
- **Título:** "Quirón" con subtítulo descriptivo
- **Marca:** Chip con "Fundación Universitaria Compensar"

#### 7.2.2 Panel de Indicadores (KPIs)

Cinco tarjetas que muestran métricas clave en tiempo real:

| Indicador | Descripción | Icono |
|-----------|-------------|-------|
| **Sedes registradas** | Total de sedes en la fuente | 🏥 |
| **Sedes con oferta quirúrgica** | Sedes que ofrecen servicios quirúrgicos | ⚕ |
| **Códigos de habilitación** | Tipos de servicio quirúrgico distintos | ▤ |
| **Sedes públicas** | Naturaleza pública | 🏛 |
| **Sedes privadas** | Naturaleza privada | ▥ |

#### 7.2.3 Panel de Trazabilidad

Información metodológica visible para garantizar transparencia:

- Entidad publicadora
- Portal de publicación
- Fecha de corte
- Cobertura geográfica
- Archivo principal
- Unidad de análisis
- Registros cargados
- Cobertura de geocodificación
- Enlace a fuente oficial
- **Advertencias metodológicas** destacadas

#### 7.2.4 Panel de Filtros

Cuatro controles de filtrado combinables:

| Filtro | Tipo | Comportamiento |
|--------|------|----------------|
| **Servicio quirúrgico** | Dropdown multi-selección | Selecciona uno o varios códigos |
| **Naturaleza jurídica** | Dropdown multi-selección | Pública, Privada, Mixta |
| **Tipo de prestador** | Dropdown multi-selección | IPS, Profesional independiente, etc. |
| **Buscar sede** | Campo de texto | Búsqueda insensible a mayúsculas/tildes |

**Botón "Limpiar filtros":** Restablece todos los criterios.

#### 7.2.5 Panel del Asistente

- **Campo de entrada:** Para escribir solicitudes
- **Botón "Hablar":** Activa el dictado por voz
- **Botón "Enviar":** Procesa la solicitud
- **Área de respuesta:** Muestra la respuesta del asistente

#### 7.2.6 Mapa Interactivo

- **Motor:** Plotly Express con scatter mapbox
- **Teselas:** CARTO (voyager o similar)
- **Centro inicial:** Bogotá D.C. (4.6486, -74.0779)
- **Zoom inicial:** 10
- **Altura:** 620px
- **Interacciones:**
  - Zoom con scroll
  - Arrastre para mover
  - Clic para ver tooltip con información de la sede
  - Enfoque programático desde el asistente

**Nota metodológica visible:** "Las sedes sin coordenadas válidas se conservan en el conjunto analítico, pero no se ubican artificialmente en el mapa."

#### 7.2.7 Tablas Descriptivas

Dos tablas actualizables según filtros:

1. **Sedes por código de habilitación:** código_servicio, nombre_servicio, sedes
2. **Sedes por naturaleza jurídica:** naturaleza, sedes

Estilizadas con colores institucionales (morado #330968).

#### 7.2.8 Panel de Exportación

Cuatro botones de descarga:

| Botón | Archivo | Contenido |
|-------|---------|-----------|
| Detalle filtrado | `quiron_detalle_oferta_quirurgica_YYYYMMDD_HHMMSS.csv` | Una fila por sede-servicio |
| Resumen por servicio | `quiron_resumen_por_servicio_YYYYMMDD_HHMMSS.csv` | Conteo por código |
| Resumen por naturaleza | `quiron_resumen_por_naturaleza_YYYYMMDD_HHMMSS.csv` | Conteo por naturaleza |
| Metadata y trazabilidad | `quiron_metadata_trazabilidad_YYYYMMDD_HHMMSS.csv` | Información metodológica |

### 7.3 Paleta de Colores

| Color | Código | Uso |
|-------|--------|-----|
| Morado profundo | `#330968` | Encabezados, botones principales |
| Morado UCompensar | `#6E48B1` | Acentos, indicadores de carga |
| Blanco | `#FFFFFF` | Fondos principales |
| Gris texto | `#6B6480` | Texto secundario |
| Lavanda claro | `#F5F3FA` | Filas alternas de tablas |
| Borde lavanda | `#E4DEF2` | Separadores |

### 7.4 Responsividad

La interfaz utiliza CSS Grid y Flexbox para adaptarse a diferentes tamaños de pantalla, aunque está optimizada principalmente para escritorio.

### 7.5 Ejemplo Visual: Lo que el Usuario Ve en Pantalla

A continuación se presenta una representación textual de lo que el dashboard muestra al usuario cuando está en funcionamiento, con **valores reales** de la fuente de datos:

#### Panel de KPIs (Valores Iniciales)

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                        INDICADORES CLAVE (KPIs)                                │
├──────────────────┬──────────────────┬─────────────────┬───────────┬───────────┤
│   🏥 SEDES       │  ⚕ OFERTA       │   ▤ CÓDIGOS     │ 🏛 PÚBLICAS│ ▥ PRIVADAS │
│   REGISTRADAS    │  QUIRÚRGICA      │   HABILITACIÓN  │           │           │
│                  │                  │                 │           │           │
│      589         │      360         │       2         │    19     │    575    │
│                  │                  │                 │           │           │
│ Sedes únicas en  │ Sedes que        │ Tipos únicos    │ Naturaleza│ Naturaleza│
│ la fuente        │ ofrecen códigos  │ de servicio     │ pública   │ privada   │
│ oficial          │ 213 o 369        │ quirúrgico      │           │           │
└──────────────────┴──────────────────┴─────────────────┴───────────┴───────────┘
```

#### Panel de Trazabilidad

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          FUENTE Y TRAZABILIDAD                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Entidad publicadora:      Secretaría Distrital de Salud de Bogotá             │
│  Portal de publicación:    Datos Abiertos Bogotá                                │
│  Fecha de corte:           01/07/2026                                           │
│  Cobertura geográfica:     Bogotá D.C.                                          │
│  Archivo principal:        cirugia-plastica-01_07_2026.csv                      │
│  Unidad de análisis:       Sede de prestador de salud                           │
│  Registros cargados:       643                                                  │
│  Sedes únicas:             589                                                  │
│  Cobertura de coordenadas: 78.1% (281 de 360 sedes quirúrgicas)                │
│                                                                                 │
│  ⚠️ ADVERTENCIA: Los resultados representan oferta registrada, no              │
│     disponibilidad efectiva ni capacidad de atención actual.                    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

#### Opciones de Filtros Disponibles

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           EXPLORAR LA OFERTA                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Servicio quirúrgico:                                                           │
│  ┌──────────────────────────────────────────────────────────────┐              │
│  │ ▼ Todos los servicios                                        │              │
│  │   • 213 - CIRUGÍA PLÁSTICA Y ESTÉTICA (98 sedes)            │              │
│  │   • 369 - CIRUGÍA PLÁSTICA Y ESTÉTICA (262 sedes)           │              │
│  └──────────────────────────────────────────────────────────────┘              │
│                                                                                 │
│  Naturaleza jurídica:                                                           │
│  ┌──────────────────────────────────────────────────────────────┐              │
│  │ ▼ Todas las naturalezas                                      │              │
│  │   • Privada (575 sedes)                                      │              │
│  │   • Pública (19 sedes)                                       │              │
│  └──────────────────────────────────────────────────────────────┘              │
│                                                                                 │
│  Tipo de prestador:                                                             │
│  ┌──────────────────────────────────────────────────────────────┐              │
│  │ ▼ Todos los tipos                                            │              │
│  │   • Profesional Independiente (315 sedes)                    │              │
│  │   • IPS - Instituciones Prestadoras de Servicios (275 sedes)│              │
│  │   • Objeto Social Diferente (4 sedes)                        │              │
│  └──────────────────────────────────────────────────────────────┘              │
│                                                                                 │
│  Buscar sede por nombre:                                                        │
│  ┌──────────────────────────────────────────────────────────────┐              │
│  │ 🔍 Escriba para buscar...                                    │              │
│  └──────────────────────────────────────────────────────────────┘              │
│                                                                                 │
│  [ 🔄 Limpiar filtros ]                                                        │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

#### Tablas Descriptivas (Estado Inicial)

```
┌──────────────────────────────────────┐  ┌──────────────────────────────────────┐
│     SEDES POR CÓDIGO DE SERVICIO     │  │     SEDES POR NATURALEZA JURÍDICA    │
├───────────────────────────┬──────────┤  ├────────────────────────────┬─────────┤
│ Código de habilitación    │  Sedes   │  │ Naturaleza                 │  Sedes  │
├───────────────────────────┼──────────┤  ├────────────────────────────┼─────────┤
│ 369 - Cirugía plástica    │   262    │  │ Privada                    │   575   │
│ 213 - Cirugía plástica    │    98    │  │ Pública                    │    19   │
├───────────────────────────┼──────────┤  ├────────────────────────────┼─────────┤
│         TOTAL             │   360*   │  │         TOTAL              │   594** │
└───────────────────────────┴──────────┘  └────────────────────────────┴─────────┘

* Total de sedes únicas (una sede puede ofrecer ambos servicios)
** Total de registros sede-servicio
```

#### Mapa Interactivo (Descripción Visual)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          DISTRIBUCIÓN GEOGRÁFICA                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────────────────────┐ │
│  │                                                                           │ │
│  │              🟣 🟣   Centro y norte de Bogotá                             │ │
│  │           🟣 🟣 🟣 🟣   (mayor concentración)                              │ │
│  │        🟣    🟣 🟣 🟣 🟣                                                    │ │
│  │            🟣  🟣 🟣 🟣 🟣    Chapinero, Usaquén                           │ │
│  │               🟣🟣 🟣                                                       │ │
│  │                🟣 🟣                                                        │ │
│  │              🟣  🟣 🟣                                                      │ │
│  │                 🟣                                                          │ │
│  │           🟣      🟣      Suba, Kennedy                                    │ │
│  │        🟣            (distribución dispersa)                               │ │
│  │      🟣                                                                     │ │
│  │                                                                           │ │
│  │   [ + ] [ - ]  Zoom        Centro: 4.6486, -74.0779 (Bogotá D.C.)       │ │
│  │                                                                           │ │
│  └───────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  Sedes visibles en mapa: 281  │  Sin coordenadas: 79  │  Cobertura: 78.1%     │
│                                                                                 │
│  ⓘ Las sedes sin coordenadas válidas se conservan en el conjunto analítico,   │
│    pero no se ubican artificialmente en el mapa.                               │
└─────────────────────────────────────────────────────────────────────────────────┘
```

#### Tooltip al Pasar el Cursor sobre un Punto del Mapa

```
┌────────────────────────────────────────────────────────┐
│  📍 ADMINISTRADORA CLÍNICA LA COLINA SAS               │
├────────────────────────────────────────────────────────┤
│  Dirección: CALLE 167 72 07 PISO 1, PISO 2...         │
│  Teléfono: 6013905355                                  │
│  Naturaleza: Privada                                   │
│  Tipo: IPS                                             │
│  Servicios:                                            │
│    • 213 - Cirugía plástica y estética                │
│                                                        │
│  Coordenadas: 4.7506, -74.0641                        │
└────────────────────────────────────────────────────────┘
```

---

## 8. Funcionalidades del Sistema

### 8.1 Consulta de Indicadores

El dashboard calcula y muestra métricas agregadas en tiempo real:

```python
# Ejemplo de cálculo en metrics.py
resumen = {
    "sedes_totales": tabla["sede_id"].nunique(),
    "sedes_con_oferta_quirurgica": tabla.loc[tabla["es_quirurgico"], "sede_id"].nunique(),
    "tipos_de_servicio_quirurgico": tabla.loc[tabla["es_quirurgico"], "codigo_servicio"].nunique(),
    "sedes_publicas": tabla.loc[tabla["naturaleza"] == "Pública", "sede_id"].nunique(),
    "sedes_privadas": tabla.loc[tabla["naturaleza"] == "Privada", "sede_id"].nunique(),
}
```

### 8.2 Filtrado Interactivo

El sistema de filtrado permite combinar múltiples criterios:

**Lógica de combinación:**
- Criterios **entre filtros distintos** se combinan con **AND**
- Opciones **dentro del mismo filtro** se combinan con **OR**

**Ejemplo:** Si se selecciona "Naturaleza = Pública" y "Servicio = 213, 369", se mostrarán las sedes que sean públicas **Y** que ofrezcan el servicio 213 **O** el servicio 369.

**Búsqueda de texto:**
- Insensible a mayúsculas/minúsculas
- Ignora tildes (normalización Unicode)
- Permite búsqueda parcial

### 8.3 Visualización Geográfica

El mapa muestra únicamente sedes con coordenadas válidas:

- **Consolidación:** Si una sede ofrece múltiples servicios, se agrupa en un solo punto
- **Tooltip:** Muestra nombre, dirección, servicios y naturaleza
- **Exclusión controlada:** Las sedes sin coordenadas permanecen en el análisis pero no aparecen en el mapa

### 8.4 Actualización Reactiva

Cuando el usuario modifica cualquier filtro:

1. Los indicadores se recalculan
2. El mapa se actualiza
3. Las tablas descriptivas se refrescan
4. El estado de filtros se muestra al usuario
5. Las exportaciones reflejarán los datos filtrados

### 8.5 Carga de Datos Propios (ETL en Vivo)

Desde el área **Proceso ETL** (`/etl`), el usuario puede cargar un archivo CSV con la misma estructura de la fuente oficial. Si el ETL es válido, **todo el dashboard se actualiza en vivo** (indicadores, filtros, mapa, tablas y exportaciones) con el nuevo conjunto de datos; si falla, se conserva el último conjunto válido y los errores se muestran sin interrumpir la aplicación. El detalle completo está en la [sección 12](#12-proceso-etl-observable).

### 8.6 Asociación de Coordenadas por Identidad

Las coordenadas del mapa se asocian mediante **coincidencia única del nombre de sede y la dirección normalizados** (normalización Unicode NFKC + casefold + compactación de espacios), no por el orden de las filas ni por la huella binaria del archivo. Esto garantiza que:

- Volver a guardar o **reordenar** un CSV no elimina coordenadas válidas.
- Las sedes **ambiguas** (nombre+dirección duplicados) o **sin coincidencia** quedan sin coordenadas, evitando ubicaciones incorrectas en el mapa.

---

## 9. Flujo de Datos y Procesamiento

### 9.1 Carga de Datos

```
┌──────────────────────────────────────────────────────────────────┐
│                        ARRANQUE (server.py)                       │
└──────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│               cargar_oferta_con_coordenadas()                     │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ 1. Leer CSV de oferta quirúrgica                           │  │
│  │    quiron/data/raw/cirugia-plastica-01_07_2026.csv        │  │
│  │                                                            │  │
│  │ 2. Leer CSV de coordenadas geocodificadas                  │  │
│  │    quiron/data/processed/sedes_geocodificadas.csv         │  │
│  │                                                            │  │
│  │ 3. Validar columnas obligatorias                           │  │
│  │                                                            │  │
│  │ 4. Transformar formato ancho → largo                       │  │
│  │    (una fila por combinación sede-servicio)                │  │
│  │                                                            │  │
│  │ 5. Marcar códigos quirúrgicos (213, 369)                   │  │
│  │                                                            │  │
│  │ 6. Unir datos de oferta con coordenadas                    │  │
│  │    (LEFT JOIN por sede_id)                                 │  │
│  │                                                            │  │
│  │ 7. Validar coordenadas (rango Bogotá)                      │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                    DataFrame unificado en memoria
```

### 9.2 Archivos CSV Fuente

| Archivo | Ubicación | Contenido |
|---------|-----------|-----------|
| `cirugia-plastica-01_07_2026.csv` | `quiron/data/raw/` | Oferta de servicios, atributos de prestadores |
| `sedes_geocodificadas.csv` | `quiron/data/processed/` | Coordenadas obtenidas de geocodificación |

### 9.3 Reglas Analíticas Importantes

> ⚠️ **Reglas que deben respetarse en cualquier modificación:**

1. **Conteo de sedes:** Siempre usar `sede_id` único, no contar filas (una sede puede tener múltiples servicios).

2. **Códigos quirúrgicos:** Solo `213` y `369` están en el alcance del análisis.

3. **Coordenadas:** No inventar ubicaciones. Las sedes sin coordenadas válidas:
   - ✅ Se incluyen en indicadores y filtros
   - ❌ No se muestran en el mapa

4. **Formato de exportación:**
   - Codificación: UTF-8 con BOM
   - Sin columna índice de pandas
   - Nombres de archivo con hora de Colombia (`America/Bogota`)

5. **Identificadores:** Mantener como texto para consistencia.

---

## 10. Asistente de Voz e Inteligencia Artificial

### 10.1 Visión General

El asistente de Quirón permite a los usuarios interactuar mediante:
- **Texto escrito:** Campo de entrada tradicional
- **Voz:** Dictado mediante Web Speech API del navegador

### 10.2 Arquitectura del Asistente

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           NAVEGADOR                                      │
│  ┌──────────────────┐                                                   │
│  │ Web Speech API   │◄─── Dictado de voz (reconocimiento local)        │
│  │ (Dictado)        │                                                   │
│  └────────┬─────────┘                                                   │
│           │ Transcripción                                                │
│           ▼                                                              │
│  ┌──────────────────┐                                                   │
│  │ asistente-voz.js │◄─── Manejo de interfaz y síntesis de voz         │
│  └────────┬─────────┘                                                   │
│           │ Texto de solicitud                                          │
└───────────┼─────────────────────────────────────────────────────────────┘
            │
            ▼ HTTP POST
┌─────────────────────────────────────────────────────────────────────────┐
│                           SERVIDOR DASH                                  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ callbacks.py → asistente.py                                       │  │
│  │                                                                    │  │
│  │  1. ¿Es solicitud de descarga local?                              │  │
│  │     → Sí: Ejecutar descarga sin llamar a Gemini                   │  │
│  │                                                                    │  │
│  │  2. ¿Menciona sede exacta georreferenciada?                       │  │
│  │     → Sí: Enfocar mapa sin llamar a Gemini                        │  │
│  │                                                                    │  │
│  │  3. Solicitud general:                                            │  │
│  │     → Llamar a API de Gemini                                      │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────────┘
            │
            ▼ API Request (solo si es necesario)
┌─────────────────────────────────────────────────────────────────────────┐
│                        GOOGLE GEMINI API                                 │
│                                                                          │
│  Prompt del sistema:                                                     │
│  "Interpreta la solicitud del usuario y devuelve un JSON con las        │
│   acciones a realizar sobre el dashboard de Quirón..."                  │
│                                                                          │
│  Respuesta estructurada (JSON):                                          │
│  {                                                                       │
│    "understood": true,                                                   │
│    "clear_filters": false,                                               │
│    "change_services": true,                                              │
│    "services": ["213"],                                                  │
│    "change_nature": true,                                                │
│    "nature": ["Pública"],                                                │
│    ...                                                                   │
│  }                                                                       │
└─────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      VALIDACIÓN Y EJECUCIÓN                              │
│                                                                          │
│  1. Validar esquema JSON                                                 │
│  2. Verificar que los valores existen en el dashboard (allowlist)        │
│  3. Rechazar valores inventados por el modelo                            │
│  4. Aplicar acciones válidas (filtros, enfoque, descarga)                │
│  5. Devolver respuesta al navegador                                      │
│  6. Leer respuesta en voz alta (speechSynthesis)                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 10.3 Acciones Soportadas

| Acción | Descripción | Ejemplo de solicitud |
|--------|-------------|---------------------|
| `clear_filters` | Limpiar todos los filtros | "Limpia todos los filtros" |
| `change_services` | Cambiar filtro de servicios | "Muestra solo cirugía plástica" |
| `change_nature` | Cambiar filtro de naturaleza | "Filtra las sedes públicas" |
| `change_providers` | Cambiar filtro de tipo prestador | "Solo IPS" |
| `change_name_search` | Buscar por nombre de sede | "Busca clínica del norte" |
| `focus_sede` | Enfocar mapa en una sede | "Amplía la Clínica Marly" |
| `download_detail` | Descargar detalle filtrado | "Descarga el detalle" |

### 10.4 Configuración

```bash
# Archivo .env (NO subir al repositorio)
GEMINI_API_KEY=tu_clave_privada_aquí
GEMINI_MODEL=gemini-3.1-flash-lite  # Opcional
```

### 10.5 Seguridad

- **No se envía audio:** Solo texto transcrito
- **Validación estricta:** Los valores deben existir en el dashboard
- **Sin ejecución arbitraria:** El asistente solo puede realizar acciones predefinidas
- **Clave protegida:** Solo existe en el servidor, nunca en el cliente

### 10.6 Ejemplo Visual: Interacción con el Asistente

#### Panel del Asistente (Estado Inicial)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           🎙️ ASISTENTE DE QUIRÓN                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Escribe tu solicitud o usa el micrófono para hablar:                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                                                                         │   │
│  │  [Escribe aquí: "muestra las sedes públicas"...]                       │   │
│  │                                                                         │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  [ 🎤 Hablar ]  [ ➤ Enviar ]                                                   │
│                                                                                 │
│  ───────────────────────────────────────────────────────────────────────────   │
│                                                                                 │
│  💬 Respuesta del asistente:                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                                                                         │   │
│  │  Hola, soy el asistente de Quirón. Puedo ayudarte a filtrar los        │   │
│  │  datos, buscar sedes específicas o descargar información.              │   │
│  │                                                                         │   │
│  │  Ejemplos de lo que puedo hacer:                                       │   │
│  │  • "Muestra solo las sedes públicas"                                   │   │
│  │  • "Filtra por cirugía plástica código 213"                            │   │
│  │  • "Busca clínica del norte"                                           │   │
│  │  • "Descarga el detalle filtrado"                                      │   │
│  │  • "Limpia todos los filtros"                                          │   │
│  │                                                                         │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

#### Ejemplos de Diálogos Reales Usuario ↔ Asistente

**Ejemplo 1: Filtrar por naturaleza**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  👤 USUARIO (texto o voz):                                                      │
│     "Muestra solo las sedes públicas"                                           │
│                                                                                 │
│  🤖 ASISTENTE (respuesta + voz):                                               │
│     "He filtrado las sedes por naturaleza pública. Ahora se muestran           │
│      19 sedes públicas que ofrecen servicios quirúrgicos en Bogotá."           │
│                                                                                 │
│  📊 CAMBIOS EN EL DASHBOARD:                                                   │
│     • KPI "Sedes públicas": 19 → 19 (sin cambio, ya estaba)                    │
│     • KPI "Sedes privadas": 575 → 0 (ocultas por filtro)                       │
│     • Mapa: Actualizado mostrando solo puntos de sedes públicas                │
│     • Tablas: Actualizadas reflejando solo naturaleza pública                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Ejemplo 2: Buscar una sede específica**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  👤 USUARIO:                                                                    │
│     "Busca clínica la colina"                                                   │
│                                                                                 │
│  🤖 ASISTENTE:                                                                 │
│     "Encontré la sede 'ADMINISTRADORA CLÍNICA LA COLINA SAS' ubicada en        │
│      CALLE 167 72 07. He ajustado la búsqueda para mostrarla."                 │
│                                                                                 │
│  📊 CAMBIOS EN EL DASHBOARD:                                                   │
│     • Campo de búsqueda: Rellenado con "clínica la colina"                     │
│     • Resultados filtrados: Solo la sede coincidente                           │
│     • Mapa: Enfocado en la ubicación de la clínica (4.7506, -74.0641)         │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Ejemplo 3: Solicitar descarga**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  👤 USUARIO:                                                                    │
│     "Descarga el detalle de las sedes filtradas"                               │
│                                                                                 │
│  🤖 ASISTENTE:                                                                 │
│     "Descargando el archivo de detalle con los filtros actuales aplicados.     │
│      El archivo se guardará como quiron_detalle_oferta_quirurgica_             │
│      20261028_214159.csv"                                                       │
│                                                                                 │
│  📊 ACCIÓN:                                                                    │
│     • Archivo CSV descargado automáticamente al navegador                      │
│     • Formato: UTF-8 con BOM, compatible con Excel                             │
│     • Contenido: Sedes según filtros activos en el momento de la descarga     │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Ejemplo 4: Limpiar filtros**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  👤 USUARIO:                                                                    │
│     "Limpia todos los filtros"                                                  │
│                                                                                 │
│  🤖 ASISTENTE:                                                                 │
│     "He restablecido todos los filtros. Ahora se muestran las 360 sedes        │
│      con oferta quirúrgica completa."                                          │
│                                                                                 │
│  📊 CAMBIOS EN EL DASHBOARD:                                                   │
│     • Todos los dropdowns: Restaurados a "Todos"                               │
│     • Campo de búsqueda: Vacío                                                 │
│     • KPIs: Valores iniciales (589 sedes, 360 quirúrgicas, etc.)              │
│     • Mapa: Todos los 281 puntos geocodificados visibles                      │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Ejemplo 5: Solicitud no comprendida**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  👤 USUARIO:                                                                    │
│     "¿Cuál es la mejor clínica de cirugía plástica?"                           │
│                                                                                 │
│  🤖 ASISTENTE:                                                                 │
│     "Lo siento, no puedo recomendar clínicas específicas ni evaluar su         │
│      calidad. Este dashboard muestra la oferta registrada de servicios         │
│      quirúrgicos, pero no incluye información sobre calidad, reputación        │
│      ni resultados clínicos.                                                    │
│                                                                                 │
│      Puedo ayudarte a:                                                         │
│      • Filtrar por tipo de servicio (código 213 o 369)                         │
│      • Ver sedes públicas o privadas                                           │
│      • Buscar una sede por nombre                                              │
│      • Descargar los datos para tu análisis"                                   │
│                                                                                 │
│  📊 CAMBIOS EN EL DASHBOARD:                                                   │
│     • Sin cambios (solicitud rechazada por estar fuera del alcance)            │
└─────────────────────────────────────────────────────────────────────────────────┘
```

#### Flujo de Dictado por Voz

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     PROCESO DE DICTADO POR VOZ                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  1️⃣ Usuario presiona [ 🎤 Hablar ]                                             │
│     └─► Botón cambia a [ 🔴 Escuchando... ]                                    │
│     └─► Navegador solicita permiso de micrófono (primera vez)                  │
│                                                                                 │
│  2️⃣ Usuario habla: "Muestra las sedes públicas"                               │
│     └─► Web Speech API transcribe en tiempo real                               │
│     └─► Texto aparece en el campo de entrada mientras habla                    │
│                                                                                 │
│  3️⃣ Usuario deja de hablar (pausa detectada)                                  │
│     └─► Botón vuelve a [ 🎤 Hablar ]                                           │
│     └─► Solicitud se envía automáticamente al servidor                         │
│                                                                                 │
│  4️⃣ Servidor procesa y responde                                               │
│     └─► Gemini interpreta el texto (si es necesario)                           │
│     └─► Respuesta aparece en el área de respuesta                              │
│                                                                                 │
│  5️⃣ Navegador lee la respuesta en voz alta                                    │
│     └─► speechSynthesis con voz en español                                     │
│     └─► Usuario escucha: "He filtrado las sedes por naturaleza pública..."     │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

#### Requisitos del Navegador para Voz

| Característica | Chrome/Edge | Firefox | Safari |
|----------------|-------------|---------|--------|
| **Web Speech API (dictado)** | ✅ Completo | ⚠️ Parcial | ⚠️ Parcial |
| **speechSynthesis (lectura)** | ✅ Completo | ✅ Completo | ✅ Completo |
| **Voz en español** | ✅ Incluida | ✅ Incluida | ✅ Incluida |

> **Recomendación:** Usar Microsoft Edge o Google Chrome para la mejor experiencia con el asistente de voz.

---

## 11. Sistema de Exportación de Datos

### 11.1 Tipos de Exportación

| Tipo | Archivo Generado | Contenido |
|------|------------------|-----------|
| **Detalle filtrado** | `quiron_detalle_oferta_quirurgica_YYYYMMDD_HHMMSS.csv` | Una fila por combinación sede-servicio |
| **Resumen por servicio** | `quiron_resumen_por_servicio_YYYYMMDD_HHMMSS.csv` | Conteo de sedes por código de habilitación |
| **Resumen por naturaleza** | `quiron_resumen_por_naturaleza_YYYYMMDD_HHMMSS.csv` | Conteo de sedes por naturaleza jurídica |
| **Metadata** | `quiron_metadata_trazabilidad_YYYYMMDD_HHMMSS.csv` | Información metodológica completa |

### 11.2 Especificaciones Técnicas

- **Codificación:** UTF-8 con BOM (Byte Order Mark) para compatibilidad con Excel
- **Separador:** Coma (,)
- **Salto de línea:** LF uniforme (\n)
- **Valores faltantes:** Cadena vacía
- **Zona horaria:** America/Bogota para nombres de archivo
- **Sin índice:** No se incluye la columna índice de pandas

### 11.3 Columnas del Detalle

```
sede_id, sede, direccion, telefono, correo, naturaleza, tipo_prestador,
codigo_servicio, nombre_servicio, latitud, longitud, coordenada_valida
```

---

## 12. Proceso ETL Observable

### 12.1 Visión General

El área **Proceso ETL** (`/etl`) convierte el proceso de datos —antes interno e invisible— en un **proceso auditable de extremo a extremo**. Cada ejecución del ETL (la inicial al arrancar la aplicación y cada carga de CSV del usuario) genera una **traza completa** con:

- **Histórico de pasos** con fase, estado, duración en milisegundos, filas/columnas de entrada y salida, filas descartadas y detalle de cada etapa.
- **Traza de mapeo de campos** que documenta cómo cada columna del origen se transforma en una columna del resultado.
- **Errores** atribuidos a la etapa exacta que falló.
- **Huella SHA-256** del contenido procesado, para identificar la fuente de forma inequívoca.
- **Historial acumulado de ejecuciones** (hasta 500 pasos) con número de ejecución, mostrando la más reciente primero.

### 12.2 Módulos de la Capa ETL

| Módulo | Elementos clave |
|--------|-----------------|
| `quiron/etl/observabilidad.py` | `NivelTraza` (info/exito/advertencia/error), `PasoETL`, `MapeoCampo`, `TrazaETL` con serialización a diccionarios aptos para `dcc.Store` |
| `quiron/etl/pipeline.py` | `ejecutar_etl(origen, nombre_fuente)` → `ResultadoETL` (tabla, traza, huella_sha256, nombre_fuente, exito); captura excepciones y las registra sin propagarlas |
| `quiron/data/loader.py` | Etapas instrumentadas mediante un observador opcional (`_ejecutar_etapa`): cada operación emite eventos con fase, estado, métricas y duración |

### 12.3 Etapas del Pipeline

Cada ejecución registra, en orden, las siguientes etapas (los nombres son los visibles en el historial):

| # | Etapa | Fase | Qué hace y qué reporta |
|---|-------|------|------------------------|
| 1 | Inicio | Proceso | Marca de inicio de la ejecución |
| 2 | Lectura del contenido | Extracción | Bytes recibidos y nombre de la fuente; el archivo se procesa en memoria, nunca se guarda en disco |
| 3 | Huella e identificación de fuente | Control | SHA-256 del contenido; indica si coincide byte a byte con el archivo incluido |
| 4 | Lectura del CSV | Extracción | Parseo con separador `;` y UTF-8; filas y columnas recibidas |
| 5 | Normalización de encabezados | Transformación | Compacta espacios/saltos de línea, descarta columnas `Unnamed`, **falla si la normalización produce encabezados duplicados** |
| 6 | Validación de estructura | Validación | Verifica las 6 columnas obligatorias (`SEDE -NOMBRE`, `DIRECCION`, `TELEFONO`, `CORREO ELECTRÓNICO`, `NATURALEZA`, `TIPO DE PRESTADOR`) |
| 7 | Limpieza de registros | Limpieza | Recorta y compacta espacios/saltos en campos de texto; **descarta filas sin nombre de sede** e informa cuántas |
| 8 | Detección de columnas de servicio | Validación | Identifica columnas cuyo nombre inicia con código numérico; falla si no hay ninguna |
| 9 | Transformación de formato ancho a largo | Transformación | Una fila por sede-servicio con marca `X`; reporta marcas aceptadas, valores no reconocidos (con muestra) y filas sin servicio marcado |
| 10 | Lectura de referencia geográfica | Extracción | Lee `sedes_geocodificadas.csv` |
| 11 | Validación de referencia geográfica | Validación | Verifica columnas obligatorias de la referencia |
| 12 | Normalización y control de coordenadas | Limpieza | Convierte latitud/longitud a numérico y valida el campo `geocodificado` |
| 13 | Normalización y depuración de identidades | Limpieza | Construye claves nombre+dirección normalizadas; descarta identidades vacías o ambiguas |
| 14 | Cruce de coordenadas | Transformación | LEFT JOIN seguro por identidad única; reporta sedes coincidentes y registros con coordenadas válidas |
| 15 | Control de integridad de la oferta | Validación | Rechaza salida vacía, columnas faltantes o registros sin `sede_id` |
| 16 | Trazabilidad de mapeo | Transformación | Documenta las relaciones origen→destino del mapeo de campos |
| 17 | Carga del conjunto transformado | Carga | Dataset final: registros, sedes únicas, sedes quirúrgicas y coordenadas válidas |

**Valores de referencia con la fuente oficial:** 643 filas de origen, 49 filas descartadas por nombre de sede vacío, 594 marcas `X` aceptadas, 360 sedes quirúrgicas y 281 registros con coordenadas válidas.

### 12.4 Interfaz del Área ETL

| Componente | Id | Contenido |
|------------|-----|-----------|
| Carga de archivo | `etl-carga-csv` | `dcc.Upload` que acepta un único `.csv` de hasta **10 MB** |
| Estado de la carga | `etl-estado` | Resultado de la última ejecución: número, fuente, duración y SHA-256 |
| Panel de errores | `etl-panel-errores` | Tarjetas de error por etapa; oculto (`etl-oculto`) cuando no hay errores |
| Histórico | `etl-tabla-historico` | Tabla con ejecución, orden, fase, paso, estado, duración, filas/columnas entrada-salida, descartes y detalle |
| Traza de mapeo | `etl-tabla-mapeo` | Tabla campo origen → campo destino → transformación → filas |

Comportamientos clave de la interfaz:

- El **historial se ordena con la ejecución más reciente primero**, sin invertir el orden interno de sus pasos.
- Las validaciones **previas al ETL** (extensión distinta de `.csv`, tamaño mayor a 10 MB, contenido no decodificable) también se registran en el historial como ejecuciones fallidas con el paso "Validación de archivo".
- Ante cualquier fallo, **se conserva el último dataset válido y su traza de mapeo**: el dashboard nunca queda vacío ni inconsistente.
- Las tablas tienen indicador de carga (`dcc.Loading`) mientras se procesa el archivo.

### 12.5 Flujo de una Carga de Usuario

```
Usuario arrastra CSV → dcc.Upload (base64)
        │
        ▼
callbacks.cargar_csv_etl()
        ├─ Validar extensión .csv          ─┐
        ├─ Validar tamaño ≤ 10 MB           ├─ Si falla: registrar en historial,
        ├─ Decodificar base64               ─┘  conservar dataset vigente
        ▼
etl.pipeline.ejecutar_etl(bytes, nombre)
        ├─ Ejecuta las 17 etapas instrumentadas
        ├─ Errores → traza.errores con fase y paso exactos
        ▼
ResultadoETL
        ├─ exito=True  → etl-dataset-activo actualizado
        │                → KPIs, mapa, tablas y exportaciones en vivo
        └─ exito=False → errores visibles + dataset anterior intacto
        ▼
_combinar_historial_etl() → acumula ejecuciones (máx. 500 pasos)
```

### 12.6 Privacidad y Límites

- El CSV cargado **permanece solo en memoria y en el estado de la sesión del navegador**; no se escribe en el servidor.
- El historial y el dataset procesado se conservan al navegar entre dashboard y ETL dentro de la misma sesión, pero **no persisten** al cerrar o recargar la pestaña (no hay base de datos de trazas).
- No hay streaming en tiempo real de eventos: la traza se muestra al finalizar la ejecución.

---

## 13. Autenticación y Administración de Usuarios

### 13.1 Visión General

La aplicación integra **Supabase Auth** para proteger todas las rutas en producción:

- **Correo y contraseña** con **MFA TOTP obligatorio** (nivel `aal2` para todas las cuentas).
- **SSO con Google** (requiere habilitar el proveedor Google en Supabase y una allowlist de correos).
- **Panel de administración** en `/admin` para gestionar usuarios.

En desarrollo local la autenticación se desactiva con `QUIRON_AUTH_ENABLED=0`; en Vercel se **activa automáticamente** (variable `VERCEL`) y la aplicación falla al arrancar si falta configuración, evitando despliegues inseguros.

### 13.2 Módulo `quiron/auth.py`

| Componente | Función |
|------------|---------|
| `load_auth_settings()` | Valida variables de entorno; exige orígenes HTTPS y correos válidos |
| `register_auth(app)` | Registra en Flask las rutas de sesión, protección global y cabeceras de seguridad |
| `proteger_aplicacion()` | Middleware que exige sesión válida en todas las rutas Dash y sus callbacks |
| `_verify_access_token()` | Valida el JWT contra las claves públicas **JWKS** de Supabase (PyJWT) |
| `_authorize_claims()` | Exige `aal2` (MFA) y, para cuentas Google, pertenencia a la allowlist |
| API `/admin` | Listar usuarios, invitar, enviar restablecimiento de contraseña, eliminar cuentas no administradoras |

### 13.3 Flujo de Sesión

1. El navegador inicia sesión con el **cliente oficial supabase-js** (fijado por versión con integrity hash) en `/login`.
2. Tras validar credenciales y TOTP, el cliente envía el token al endpoint de sesión del servidor.
3. El servidor verifica el JWT (JWKS, emisor, audiencia, `aal2`) y emite una **cookie `HttpOnly`, `SameSite=Lax` y `Secure`** bajo HTTPS.
4. `assets/auth-session.js` renueva la cookie cuando supabase-js refresca el token; la sesión de Supabase vive solo en el `sessionStorage` de la pestaña.
5. Al volver a una pestaña con cookie vencida, se intenta renovar la sesión antes de cargar el dashboard.

### 13.4 Variables de Entorno de Producción

| Variable | Propósito |
|----------|-----------|
| `SUPABASE_URL` | Origen HTTPS del proyecto Supabase |
| `SUPABASE_ANON_KEY` | Clave pública (`sb_publishable_...` o `anon` heredada) |
| `SUPABASE_SERVICE_ROLE_KEY` | Clave privilegiada (`sb_secret_...` o `service_role`), **solo del lado servidor** |
| `QUIRON_BASE_URL` | Origen público exacto de la aplicación |
| `QUIRON_ADMIN_EMAILS` | Correos administradores iniciales (separados por comas) |
| `QUIRON_GOOGLE_ALLOWED_EMAILS` | Allowlist para SSO Google; vacía desactiva el botón |

Las claves modernas se envían solo en el encabezado `apikey`; las heredadas también como `Authorization: Bearer`.

### 13.5 Panel de Administración (`/admin`)

Permite a cuentas administradoras:

- **Invitar usuarios** (reciben enlace para establecer contraseña; deben registrar TOTP en el primer acceso).
- **Ver** correo, rol, fecha de creación y último inicio de sesión.
- **Enviar enlaces** de restablecimiento de contraseña.
- **Eliminar** cuentas no administradoras.

La clave `SUPABASE_SERVICE_ROLE_KEY` se usa exclusivamente para estas operaciones del lado servidor y nunca se expone al navegador.

### 13.6 Cabeceras y Prácticas de Seguridad

- Cabeceras de seguridad agregadas a todas las respuestas (`agregar_cabeceras_seguridad`).
- Validación de mismo origen en los endpoints de sesión.
- Registro público de Supabase desactivado: solo cuentas creadas o invitadas.
- El audio del dictado nunca sale del navegador; a Gemini solo llega texto.

---

## 14. Pruebas y Validación

### 14.1 Estrategia de Pruebas

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PIRÁMIDE DE PRUEBAS                              │
│                                                                      │
│                         ┌─────┐                                     │
│                        /       \                                     │
│                       /  E2E    \   ← Playwright (12 escenarios)    │
│                      /  (12)     \                                   │
│                     ─────────────                                    │
│                    /             \                                   │
│                   /  Integración  \  ← Carga ETL vía endpoint Dash, │
│                  /                 \    autenticación, entrypoint    │
│                 ─────────────────────                                │
│                /                     \                               │
│               /   Unitarias (164)     \  ← pytest                   │
│              / filtros, exportación,   \                             │
│             / metadata, ETL, auth, mapa \                            │
│            ─────────────────────────────                             │
└─────────────────────────────────────────────────────────────────────┘
```

### 14.2 Pruebas Unitarias Python

**Instalación:**
```bash
pip install -r requirements.txt   # incluye pytest y pytest-cov
```

**Ejecución:**
```bash
# Todas las pruebas (164 recolectadas)
python -m pytest

# Una suite específica
python -m pytest tests/test_etl.py

# Con cobertura (configurada en pyproject.toml, con ramas)
python -m pytest --cov=quiron
```

**Suites disponibles:**

| Suite | Prueba |
|-------|--------|
| `test_filtros.py` | Opciones de filtro, aplicación de filtros, normalización de texto, conteo de sedes |
| `test_exportacion.py` | Preparación de detalle, deduplicación, resúmenes, conversión a CSV |
| `test_metadata.py` | Metadata estática, valores dinámicos, fuente y cobertura |
| `test_asistente.py` | Validación de comandos, allowlist, respuestas simuladas, manejo de errores |
| `test_normalizador.py` | Normalización de direcciones bogotanas, casos reales |
| `test_mapa.py` | Construcción del mapa y manejo de sedes sin coordenadas |
| `test_etl.py` | Pipeline completo: éxito con archivo incluido y bytes en memoria, traza de limpieza y métricas por etapa, encabezados duplicados, marcas no reconocidas, salida vacía, atribución de errores a la etapa exacta, coordenadas por identidad (reordenamiento y ambigüedad), serialización de la traza |
| `test_etl_upload.py` | Integración vía endpoint `/_dash-update-component`: carga válida activa el dataset, esquema inválido y extensión inválida conservan el estado y acumulan el historial |
| `test_auth.py` | Configuración, validación de variables, autorización por claims, allowlist de Google, rol administrador |
| `test_vercel_entrypoint.py` | El punto de entrada WSGI (`run.app`) sirve el dashboard |

### 14.3 Pruebas E2E con Playwright

**Instalación:**
```bash
npm install
```

**Ejecución:**
```bash
npm run test:e2e
```

**Escenarios cubiertos (numeración de los archivos spec):**

| # | Escenario | Archivo | Descripción |
|---|-----------|---------|-------------|
| 01 | Carga inicial | `dashboard.spec.js` | Dashboard se renderiza correctamente |
| 02 | Filtrar y restablecer | `dashboard.spec.js` | Aplicar y limpiar filtros actualiza indicadores y mapa |
| 03 | Búsqueda sin coincidencias | `dashboard.spec.js` | Búsqueda vacía muestra mensaje y se recupera |
| 04 | Descarga detalle | `exportaciones.spec.js` | Archivo CSV se descarga correctamente |
| 05 | Descarga servicio | `exportaciones.spec.js` | Resumen por servicio funciona |
| 06 | Descarga naturaleza | `exportaciones.spec.js` | Resumen por naturaleza funciona |
| 07 | Descarga metadata | `exportaciones.spec.js` | Metadata se descarga |
| 08 | Asistente descarga | `asistente.spec.js` | Comando de descarga local funciona |
| 09 | Asistente texto | `ai.spec.js` | Solicitud procesada por Gemini mock aplica una acción |
| 10 | Asistente voz | `asistente.spec.js` | Dictado y respuesta hablada funcionan |
| 11* | Gemini real | `ai-live.spec.js` | Integración con API real (opcional) |
| 12 | Proceso ETL | `etl.spec.js` | Navegación a `/etl`, histórico y mapeo iniciales, carga de CSV válido con actualización en vivo del dashboard, carga de CSV con esquema inválido (error visible + conservación del dataset) y persistencia al navegar entre vistas |

> *La prueba 11 requiere `E2E_LIVE_GEMINI=1` y consume cuota.

**Prueba con Gemini real (PowerShell):**
```powershell
$env:E2E_LIVE_GEMINI = "1"
npm run test:e2e
Remove-Item Env:E2E_LIVE_GEMINI
```

### 14.4 Requisitos de Entorno para Pruebas

| Requisito | Windows | Linux/macOS |
|-----------|---------|-------------|
| Navegador | Microsoft Edge | Chromium (`npx playwright install chromium`) |
| Video de voz | FFmpeg en PATH | FFmpeg en PATH |
| Voz española | Voz del sistema | Voz del sistema |
| Red | Teselas CARTO | Teselas CARTO |

### 14.5 Artefactos de Prueba

Los resultados se generan en `reportes/pruebas_funcionales/`:
- Capturas PNG de cada paso
- PDFs con flujo completo
- Videos MP4 con narración (pruebas de voz)

---

## 15. Despliegue y Configuración

### 15.1 Ejecución Local

```bash
# 1. Clonar repositorio
git clone https://github.com/JhonAlejandroBetancourt/Proyecto-fin-de-grado.git
cd Proyecto-fin-de-grado

# 2. Crear entorno virtual (recomendado)
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/macOS

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar entorno local (asistente opcional, auth desactivada)
copy .env.example .env
# Editar .env: GEMINI_API_KEY y dejar QUIRON_AUTH_ENABLED=0

# 5. Ejecutar
python run.py
# → http://localhost:8050
```

### 15.2 Despliegue en Producción (Vercel)

El proyecto se despliega en **Vercel** con integración continua desde GitHub:

| Aspecto | Configuración |
|---------|---------------|
| **Proyecto Vercel** | `proyecto-fin-de-grado`, vinculado al repositorio GitHub |
| **Rama de producción** | `main`: cada merge genera un deployment de producción |
| **Ramas feature** | Generan deployments de **preview** automáticos |
| **Entrypoint WSGI** | `run:app` (declarado en `pyproject.toml`, sección `[tool.vercel]`) |
| **Python** | 3.11 (`runtime.txt`) |

**Variables de entorno requeridas en Vercel** (la app falla al arrancar si faltan, porque `VERCEL` activa la autenticación):

| Variable | Propósito |
|----------|-----------|
| `GEMINI_API_KEY` | Asistente (opcional) |
| `SUPABASE_URL`, `SUPABASE_ANON_KEY` | Conexión pública a Supabase |
| `SUPABASE_SERVICE_ROLE_KEY` | API administrativa (solo servidor) |
| `QUIRON_BASE_URL` | Origen público exacto del despliegue |
| `QUIRON_ADMIN_EMAILS` | Administradores iniciales |
| `QUIRON_GOOGLE_ALLOWED_EMAILS` | Allowlist de SSO Google |

**Flujo de trabajo con ramas:** cada mejora se desarrolla en una rama `feat/...`, `fix/...` o `docs/...`, se valida con la suite completa y la prueba E2E correspondiente, y se integra a `main` para desplegar. Ejemplos reales del historial: `feat/auth-supabase`, `feat/separated-etl-workspace`, `feat/full-etl-process-observability`, `fix/supabase-modern-api-key-headers`, `fix/vercel-wsgi-entrypoint`.

### 15.3 Despliegue Alternativo (Render)

| Opción | Valor |
|--------|-------|
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn run:server --bind 0.0.0.0:$PORT --workers 1 --timeout 120` |
| **Python Version** | 3.11 |

### 15.4 Consideraciones de Producción

> ⚠️ **Advertencias importantes:**

1. **Autenticación obligatoria en Vercel:** La aplicación exige sesión válida con MFA (`aal2`) en todas las rutas; el arranque falla si falta configuración.
2. **Cuota de Gemini:** Controlar uso para evitar costos inesperados.
3. **Datos versionados:** Los CSV deben estar en el repositorio.
4. **Python 3.11:** pandas 2.2.2 puede fallar en versiones más nuevas.
5. **Clave service_role:** Nunca exponerla al navegador ni guardarla en el repositorio.
6. **SSO Google:** Requiere habilitar el proveedor en Supabase (Authentication → Sign In / Providers), configurar las credenciales OAuth de Google Cloud y registrar las URLs de redirección permitidas.

---

## 16. Limitaciones y Alcance

### 16.1 Limitaciones Técnicas

| Limitación | Descripción |
|------------|-------------|
| **Geocodificación incompleta** | No todas las sedes tienen coordenadas válidas (281 de 360 sedes quirúrgicas, 78.1%) |
| **Dependencia de red** | Mapa requiere teselas de CARTO, Gemini y Supabase requieren conexión |
| **Voz del navegador** | Dictado depende de Web Speech API (Chrome/Edge) |
| **Datos al arrancar** | El dataset base se carga al inicio; el usuario puede sustituirlo cargando un CSV al ETL, pero el cambio vive solo en la sesión |
| **Trazas ETL sin persistencia** | El historial de ejecuciones se conserva en la sesión del navegador (máx. 500 pasos) y se pierde al recargar |
| **Carga ETL acotada** | Un único archivo `.csv` de máximo 10 MB por carga |

### 16.2 Limitaciones Analíticas

> ⚠️ **Los resultados son oferta registrada, NO:**

- ❌ Disponibilidad en tiempo real
- ❌ Capacidad efectiva de atención
- ❌ Número de procedimientos realizados
- ❌ Tiempos de espera
- ❌ Demanda de servicios
- ❌ Resultados clínicos
- ❌ Calidad del servicio

### 16.3 Dependencias Externas

| Servicio | Uso | Impacto si falla |
|----------|-----|------------------|
| CARTO | Teselas del mapa | Mapa no se renderiza |
| Google Gemini | Interpretación de comandos | Asistente no funciona |
| Nominatim | Geocodificación (preproceso) | Solo afecta regeneración de coordenadas |
| Supabase Auth | Autenticación y administración | No es posible iniciar sesión en producción |
| Vercel | Hosting de producción | Aplicación inaccesible en Internet |

### 16.4 Fecha de Corte de Datos

- **Fecha declarada:** 01/07/2026
- **Origen:** Nombre del archivo fuente
- **Verificación recomendada:** Contrastar con documentación oficial del recurso

---

## 17. Glosario Técnico

| Término | Definición |
|---------|------------|
| **aal2** | Authenticator Assurance Level 2: nivel de sesión que exige segundo factor (MFA) |
| **Callback** | Función que responde a eventos del usuario en Dash |
| **Dash** | Framework Python para crear aplicaciones web analíticas |
| **DataFrame** | Estructura de datos tabular de pandas |
| **E2E** | End-to-End, pruebas que simulan usuario real |
| **ETL** | Extract, Transform, Load: proceso de extracción, transformación y carga de datos |
| **Geocodificación** | Proceso de convertir direcciones en coordenadas |
| **Gunicorn** | Servidor WSGI para aplicaciones Python en producción |
| **Huella SHA-256** | Resumen criptográfico que identifica de forma única el contenido de un archivo |
| **IPS** | Institución Prestadora de Servicios de Salud |
| **JWKS** | JSON Web Key Set: claves públicas para verificar firmas de JWT |
| **JWT** | JSON Web Token: token firmado que transporta la identidad del usuario |
| **KPI** | Key Performance Indicator, indicador clave |
| **Layout** | Estructura visual de la interfaz |
| **MFA / TOTP** | Autenticación multifactor con códigos temporales de una aplicación autenticadora |
| **Nominatim** | Servicio de geocodificación de OpenStreetMap |
| **Observabilidad** | Capacidad de inspeccionar el estado interno de un proceso a partir de sus trazas y métricas |
| **Plotly** | Biblioteca de visualizaciones interactivas |
| **Playwright** | Framework de automatización de navegadores |
| **Sede quirúrgica** | IPS que ofrece servicios con códigos 213 o 369 |
| **SSO** | Single Sign-On: inicio de sesión con un proveedor de identidad externo (Google) |
| **Supabase** | Plataforma backend con autenticación, base de datos y API administrativa |
| **Tesela** | Fragmento de imagen que compone un mapa digital |
| **Traza de mapeo** | Registro de cómo cada campo del origen se transforma en un campo del resultado |
| **Trazabilidad** | Documentación del origen y procesamiento de datos |
| **Vercel** | Plataforma de despliegue en la nube con integración continua |
| **Web Speech API** | API del navegador para reconocimiento y síntesis de voz |
| **WSGI** | Web Server Gateway Interface, estándar Python para servidores |

---

## 18. Referencias

### 18.1 Archivos Principales del Proyecto

| Archivo | Propósito |
|---------|-----------|
| `run.py` | Punto de entrada para ejecución local, Gunicorn y Vercel (`run:app`) |
| `requirements.txt` | Dependencias Python del proyecto |
| `runtime.txt` | Versión de Python (3.11) |
| `pyproject.toml` | Configuración de pytest, coverage y entrypoint de Vercel |
| `package.json` | Dependencias Node/Playwright |
| `playwright.config.js` | Configuración de pruebas E2E (servidor mock de Gemini incluido) |
| `.env.example` | Plantilla de variables de entorno (Gemini + Supabase) |
| `README.md` | Guía de uso, autenticación, ETL y pruebas |

### 18.2 Documentación Relacionada

| Recurso | URL |
|---------|-----|
| **Fuente de datos** | https://datosabiertos.bogota.gov.co/dataset/ips-servicios-cirugia-estetica |
| **Dash Documentation** | https://dash.plotly.com/ |
| **Plotly Python** | https://plotly.com/python/ |
| **Google Gemini API** | https://ai.google.dev/ |
| **Playwright** | https://playwright.dev/ |
| **Supabase Auth** | https://supabase.com/docs/guides/auth |
| **Vercel** | https://vercel.com/docs |
| **Render** | https://render.com/docs |

### 18.3 Contacto del Proyecto

- **Repositorio:** https://github.com/JhonAlejandroBetancourt/Proyecto-fin-de-grado
- **Institución:** Fundación Universitaria Compensar

---

## Apéndice A: Diagrama de Flujo de Usuario

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FLUJO TÍPICO DE USUARIO                             │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────┐
    │ INICIO  │
    └────┬────┘
         │
         ▼
    ┌─────────────────────┐
    │ Abrir dashboard     │
    │ http://localhost:   │
    │ 8050                 │
    └──────────┬──────────┘
               │
               ▼
    ┌─────────────────────┐
    │ Ver indicadores     │
    │ generales (KPIs)    │
    └──────────┬──────────┘
               │
               ▼
    ┌─────────────────────┐     ┌─────────────────────┐
    │ ¿Filtrar datos?     │────►│ Aplicar filtros     │
    │                     │ Sí  │ (servicio,          │
    └──────────┬──────────┘     │  naturaleza, etc.)  │
               │ No             └──────────┬──────────┘
               │                           │
               ▼                           ▼
    ┌─────────────────────┐     ┌─────────────────────┐
    │ Explorar mapa       │     │ Ver resultados      │
    │ interactivo         │◄────│ actualizados        │
    └──────────┬──────────┘     └─────────────────────┘
               │
               ▼
    ┌─────────────────────┐     ┌─────────────────────┐
    │ ¿Usar asistente?    │────►│ Dictar o escribir   │
    │                     │ Sí  │ solicitud           │
    └──────────┬──────────┘     └──────────┬──────────┘
               │ No                        │
               │                           ▼
               │                ┌─────────────────────┐
               │                │ Respuesta del       │
               │                │ asistente           │
               │                └──────────┬──────────┘
               │                           │
               ▼                           ▼
    ┌─────────────────────┐     ┌─────────────────────┐
    │ ¿Descargar datos?   │────►│ Seleccionar tipo    │
    │                     │ Sí  │ de descarga         │
    └──────────┬──────────┘     └──────────┬──────────┘
               │ No                        │
               │                           ▼
               │                ┌─────────────────────┐
               │                │ Archivo CSV         │
               │                │ descargado          │
               ▼                └─────────────────────┘
    ┌─────────┐
    │   FIN   │
    └─────────┘
```

---

## Apéndice B: Guía Rápida de Comandos

### Desarrollo Local

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar aplicación
python run.py

# Ejecutar pruebas unitarias
python -m pytest

# Ejecutar pruebas E2E
npm install
npm run test:e2e
```

### Configuración de Asistente y Autenticación Local

```bash
# Copiar plantilla
copy .env.example .env

# Editar .env y agregar:
# GEMINI_API_KEY=tu_clave_aquí
# QUIRON_AUTH_ENABLED=0   (desactiva la autenticación en desarrollo)
```

### Rutas de la Aplicación

```
/        → Dashboard (indicadores, filtros, mapa, exportación, asistente)
/etl     → Proceso ETL (carga CSV, historial, traza de mapeo, errores)
/admin   → Administración de usuarios (requiere rol administrador)
/login   → Inicio de sesión (correo/contraseña + TOTP, o Google SSO)
/logout  → Cierre de sesión
```

### Despliegue

```bash
# Producción: push/merge a main → Vercel despliega automáticamente
git checkout main
git merge feat/mi-rama
git push origin main

# Alternativa Render:
# Build:  pip install -r requirements.txt
# Start:  gunicorn run:server --bind 0.0.0.0:$PORT --workers 1 --timeout 120
```

---

## Apéndice C: Guía para Actualizar el Documento de Grado (Word)

Esta sección orienta a un asistente de IA que use este archivo para redactar o actualizar el documento formal del trabajo de grado.

### C.1 Correspondencia Sugerida de Capítulos

| Capítulo típico del documento | Secciones de esta guía |
|-------------------------------|------------------------|
| Introducción y planteamiento del problema | 1, 2 |
| Objetivos | 3 |
| Marco teórico / tecnológico | 5, 17 (glosario) |
| Diseño y arquitectura | 4, 6, 7 |
| Desarrollo e implementación | 8, 9, 10, 11, **12 (ETL)**, **13 (Autenticación)** |
| Pruebas y validación | 14 |
| Despliegue | 15 |
| Limitaciones y trabajo futuro | 16 |
| Referencias | 18 |

### C.2 Novedades que Deben Reflejarse en el Documento

Si el documento Word fue redactado antes de noviembre de 2026, estas funcionalidades probablemente **no están documentadas** y deben incorporarse:

1. **Aplicación multipágina** con navegación entre `/`, `/etl` y `/admin` (sección 1.2.1).
2. **Proceso ETL observable completo** (sección 12): 17 etapas instrumentadas, historial de ejecuciones, traza de mapeo de campos, huella SHA-256, métricas de limpieza y conservación del último dataset válido ante fallos.
3. **Carga de CSV por el usuario** con actualización en vivo del dashboard (secciones 8.5 y 12.5).
4. **Asociación de coordenadas por identidad** nombre+dirección en lugar de orden de filas (sección 8.6).
5. **Autenticación con Supabase** (sección 13): correo/contraseña, MFA TOTP obligatoria (`aal2`), SSO Google con allowlist, cookie `HttpOnly` y validación JWT por JWKS.
6. **Panel de administración de usuarios** `/admin` (sección 13.5).
7. **Despliegue en producción en Vercel** con integración continua por ramas (sección 15.2); Render queda como alternativa.
8. **Suite de pruebas ampliada**: 164 pruebas unitarias/integración y 12 escenarios E2E, incluyendo el escenario 12 de ETL (sección 14).

### C.3 Criterios de Redacción

- Usar las **cifras verificadas** de esta guía (589 sedes, 360 quirúrgicas, 281 georreferenciadas, 78.1% cobertura, 643 registros, códigos 213 y 369).
- Mantener siempre la **advertencia metodológica**: oferta registrada ≠ disponibilidad efectiva.
- Citar nombres reales de módulos, rutas e identificadores tal como aparecen aquí.
- Las capturas de pantalla para el documento pueden tomarse de las evidencias en `reportes/pruebas_funcionales/` o del despliegue en producción.
- No incluir claves, tokens ni valores de variables de entorno reales en el documento.

---

*Documento generado para el Trabajo de Grado - Fundación Universitaria Compensar*
*Última actualización: Noviembre 2026*
