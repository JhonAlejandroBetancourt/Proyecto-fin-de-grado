# Guía Completa del Proyecto Quirón

## Documentación Técnica para Trabajo de Grado

**Título del Proyecto:** Dashboard para el análisis de la oferta registrada de servicios quirúrgicos de las IPS de Bogotá D.C.

**Institución:** Fundación Universitaria Compensar

**Fecha de Documentación:** Octubre 2026

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
12. [Pruebas y Validación](#12-pruebas-y-validación)
13. [Despliegue y Configuración](#13-despliegue-y-configuración)
14. [Limitaciones y Alcance](#14-limitaciones-y-alcance)
15. [Glosario Técnico](#15-glosario-técnico)
16. [Referencias](#16-referencias)

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
6. **Documentar metodológicamente** las fuentes y limitaciones del análisis.
7. **Garantizar la calidad** mediante pruebas automatizadas.

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

### 4.2 Patrón de Diseño

El proyecto sigue una arquitectura **MVC adaptada para Dash**:

- **Modelo (Model):** `loader.py`, `metrics.py`, `filtros.py` - Gestión de datos.
- **Vista (View):** `layout.py`, `assets/` - Definición de la interfaz.
- **Controlador (Controller):** `callbacks.py`, `asistente.py` - Lógica de interacción.

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
| **Framework Web** | Dash | 2.x | Aplicación web reactiva |
| **Manipulación de Datos** | pandas | 2.2.2 | Procesamiento de CSV |
| **Visualizaciones** | Plotly | 5.x | Gráficos y mapas interactivos |
| **Servidor Producción** | Gunicorn | - | WSGI para despliegue |
| **Pruebas E2E** | Playwright | Node.js | Pruebas de navegador |
| **IA/Asistente** | Google Gemini | API | Interpretación de comandos |

### 5.2 Servicios Externos

| Servicio | Uso en el Proyecto |
|----------|-------------------|
| **CARTO** | Teselas del mapa base (capa cartográfica) |
| **OpenStreetMap Nominatim** | Geocodificación de direcciones (preprocesado) |
| **Google Gemini** | Interpretación de solicitudes en lenguaje natural |
| **Web Speech API** | Dictado y síntesis de voz en el navegador |

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
├── run.py                          # Punto de entrada principal
├── requirements.txt                # Dependencias Python
├── runtime.txt                     # Versión de Python (3.11)
├── package.json                    # Dependencias Node/Playwright
├── playwright.config.js            # Configuración de pruebas E2E
├── .env.example                    # Plantilla de variables de entorno
│
├── quiron/                         # 📦 PAQUETE PRINCIPAL
│   ├── _init_.py                   # Inicializador del paquete
│   ├── server.py                   # Orquestador de la aplicación
│   ├── layout.py                   # Estructura visual (interfaz)
│   ├── callbacks.py                # Lógica de interacciones
│   ├── filtros.py                  # Sistema de filtrado
│   ├── exportacion.py              # Generación de CSV de salida
│   ├── metadata.py                 # Trazabilidad y fuente de datos
│   ├── asistente.py                # Integración con Gemini
│   ├── theme.py                    # Configuración de colores/tema
│   │
│   ├── data/                       # 📁 CAPA DE DATOS
│   │   ├── loader.py               # Carga y validación de CSV
│   │   ├── metrics.py              # Cálculo de indicadores
│   │   ├── raw/                    # Archivos CSV originales
│   │   │   └── cirugia-plastica-01_07_2026.csv
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
│   └── assets/                     # 🎨 RECURSOS FRONTEND
│       ├── styles.css              # Estilos CSS del dashboard
│       ├── asistente-voz.js        # Lógica de voz del navegador
│       └── mapa-tooltip.js         # Comportamiento del mapa
│
├── tests/                          # 🧪 PRUEBAS
│   ├── test_filtros.py             # Pruebas de filtrado
│   ├── test_exportacion.py         # Pruebas de exportación
│   ├── test_metadata.py            # Pruebas de metadata
│   ├── test_asistente.py           # Pruebas del asistente
│   ├── test_normalizador.py        # Pruebas de normalización
│   └── e2e/                        # Pruebas de navegador
│       ├── dashboard.spec.js       # Carga del dashboard
│       ├── asistente.spec.js       # Asistente de voz
│       ├── exportaciones.spec.js   # Descargas CSV
│       └── support/                # Mock de Gemini y utilidades
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
| `layout.py` | Define toda la estructura visual HTML/Dash sin lógica de datos |
| `callbacks.py` | Conecta controles con acciones: filtrado, actualización de gráficos, descargas |
| `filtros.py` | Implementa la lógica de filtrado y genera opciones válidas |
| `loader.py` | Lee, valida y transforma los archivos CSV fuente |
| `metrics.py` | Calcula conteos y estadísticas agregadas |
| `exportacion.py` | Prepara DataFrames para descarga en formato CSV |
| `metadata.py` | Centraliza información de trazabilidad y advertencias metodológicas |
| `asistente.py` | Procesa solicitudes con Gemini y valida acciones permitidas |
| `mapa.py` | Construye la figura del mapa interactivo con Plotly |

---

## 7. Descripción de la Interfaz Visual

### 7.1 Composición General de la Interfaz

La interfaz de Quirón está organizada en **secciones verticales** que guían al usuario desde la información general hasta los detalles:

```
┌─────────────────────────────────────────────────────────────────────┐
│  ⚕ QUIRÓN - Radar de oferta quirúrgica de las IPS de Bogotá D.C.   │
│                    Fundación Universitaria Compensar                 │
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

## 12. Pruebas y Validación

### 12.1 Estrategia de Pruebas

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PIRÁMIDE DE PRUEBAS                              │
│                                                                      │
│                         ┌─────┐                                     │
│                        /       \                                     │
│                       /  E2E    \   ← Playwright (navegador)        │
│                      /  (11+)    \                                   │
│                     ─────────────                                    │
│                    /             \                                   │
│                   /  Integración  \  ← Callbacks, asistente         │
│                  /     (~20)       \                                 │
│                 ─────────────────────                                │
│                /                     \                               │
│               /    Unitarias (~50+)   \  ← pytest                   │
│              /  filtros, exportación,  \                             │
│             /   metadata, normalizador  \                            │
│            ─────────────────────────────                             │
└─────────────────────────────────────────────────────────────────────┘
```

### 12.2 Pruebas Unitarias Python

**Instalación:**
```bash
python -m pip install pytest
```

**Ejecución:**
```bash
# Todas las pruebas
python -m pytest

# Una suite específica
python -m pytest tests/test_filtros.py

# Con cobertura (requiere pytest-cov)
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

### 12.3 Pruebas E2E con Playwright

**Instalación:**
```bash
npm install
```

**Ejecución:**
```bash
npm run test:e2e
```

**Escenarios cubiertos:**

| # | Escenario | Descripción |
|---|-----------|-------------|
| 1 | Carga inicial | Dashboard se renderiza correctamente |
| 2 | Filtrado | Aplicar filtros actualiza indicadores y mapa |
| 3 | Restablecimiento | Limpiar filtros restaura estado inicial |
| 4 | Búsqueda vacía | Búsqueda sin resultados muestra mensaje |
| 5 | Descarga detalle | Archivo CSV se descarga correctamente |
| 6 | Descarga servicio | Resumen por servicio funciona |
| 7 | Descarga naturaleza | Resumen por naturaleza funciona |
| 8 | Descarga metadata | Metadata se descarga |
| 9 | Asistente descarga | Comando de descarga funciona |
| 10 | Asistente texto | Solicitud procesada por Gemini mock |
| 11 | Asistente voz | Dictado y síntesis funcionan |
| 12* | Gemini real | Integración con API real (opcional) |

> *La prueba 12 requiere configuración especial y consume cuota.

**Prueba con Gemini real (PowerShell):**
```powershell
$env:E2E_LIVE_GEMINI = "1"
npm run test:e2e
Remove-Item Env:E2E_LIVE_GEMINI
```

### 12.4 Requisitos de Entorno para Pruebas

| Requisito | Windows | Linux/macOS |
|-----------|---------|-------------|
| Navegador | Microsoft Edge | Chromium (`npx playwright install chromium`) |
| Video de voz | FFmpeg en PATH | FFmpeg en PATH |
| Voz española | Voz del sistema | Voz del sistema |
| Red | Teselas CARTO | Teselas CARTO |

### 12.5 Artefactos de Prueba

Los resultados se generan en `reportes/pruebas_funcionales/`:
- Capturas PNG de cada paso
- PDFs con flujo completo
- Videos MP4 con narración (pruebas de voz)

---

## 13. Despliegue y Configuración

### 13.1 Ejecución Local

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

# 4. Configurar asistente (opcional)
copy .env.example .env
# Editar .env y agregar GEMINI_API_KEY

# 5. Ejecutar
python run.py
# → http://localhost:8050
```

### 13.2 Despliegue en Render

**Paso 1:** Crear Web Service conectado al repositorio

**Paso 2:** Configurar opciones:

| Opción | Valor |
|--------|-------|
| **Language** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn run:server --bind 0.0.0.0:$PORT --workers 1 --timeout 120` |
| **Python Version** | 3.11 |

**Paso 3:** Variables de entorno (si se usa asistente):

| Variable | Valor |
|----------|-------|
| `GEMINI_API_KEY` | Tu clave de API |
| `PYTHON_VERSION` | `3.11.11` (si runtime.txt no funciona) |

### 13.3 Consideraciones de Producción

> ⚠️ **Advertencias importantes:**

1. **Sin autenticación:** La aplicación es pública si se despliega en Internet
2. **Cuota de Gemini:** Controlar uso para evitar costos inesperados
3. **Plan gratuito:** Render puede suspender servicios inactivos
4. **Datos versionados:** Los CSV deben estar en el repositorio
5. **Python 3.11:** pandas 2.2.2 puede fallar en versiones más nuevas

---

## 14. Limitaciones y Alcance

### 14.1 Limitaciones Técnicas

| Limitación | Descripción |
|------------|-------------|
| **Geocodificación incompleta** | No todas las sedes tienen coordenadas válidas |
| **Dependencia de red** | Mapa requiere teselas de CARTO, Gemini requiere conexión |
| **Voz del navegador** | Dictado depende de Web Speech API (Chrome/Edge) |
| **Sin tiempo real** | Datos estáticos cargados al arrancar |
| **Sin autenticación** | No hay control de acceso para usuarios |

### 14.2 Limitaciones Analíticas

> ⚠️ **Los resultados son oferta registrada, NO:**

- ❌ Disponibilidad en tiempo real
- ❌ Capacidad efectiva de atención
- ❌ Número de procedimientos realizados
- ❌ Tiempos de espera
- ❌ Demanda de servicios
- ❌ Resultados clínicos
- ❌ Calidad del servicio

### 14.3 Dependencias Externas

| Servicio | Uso | Impacto si falla |
|----------|-----|------------------|
| CARTO | Teselas del mapa | Mapa no se renderiza |
| Google Gemini | Interpretación de comandos | Asistente no funciona |
| Nominatim | Geocodificación (preproceso) | Solo afecta regeneración de coordenadas |

### 14.4 Fecha de Corte de Datos

- **Fecha declarada:** 01/07/2026
- **Origen:** Nombre del archivo fuente
- **Verificación recomendada:** Contrastar con documentación oficial del recurso

---

## 15. Glosario Técnico

| Término | Definición |
|---------|------------|
| **Callback** | Función que responde a eventos del usuario en Dash |
| **Dash** | Framework Python para crear aplicaciones web analíticas |
| **DataFrame** | Estructura de datos tabular de pandas |
| **E2E** | End-to-End, pruebas que simulan usuario real |
| **Geocodificación** | Proceso de convertir direcciones en coordenadas |
| **Gunicorn** | Servidor WSGI para aplicaciones Python en producción |
| **IPS** | Institución Prestadora de Servicios de Salud |
| **KPI** | Key Performance Indicator, indicador clave |
| **Layout** | Estructura visual de la interfaz |
| **Nominatim** | Servicio de geocodificación de OpenStreetMap |
| **Plotly** | Biblioteca de visualizaciones interactivas |
| **Playwright** | Framework de automatización de navegadores |
| **Render** | Plataforma de despliegue en la nube |
| **Sede quirúrgica** | IPS que ofrece servicios con códigos 213 o 369 |
| **Tesela** | Fragmento de imagen que compone un mapa digital |
| **Trazabilidad** | Documentación del origen y procesamiento de datos |
| **Web Speech API** | API del navegador para reconocimiento y síntesis de voz |
| **WSGI** | Web Server Gateway Interface, estándar Python para servidores |

---

## 16. Referencias

### 16.1 Archivos Principales del Proyecto

| Archivo | Propósito |
|---------|-----------|
| `run.py` | Punto de entrada para ejecución local y Gunicorn |
| `requirements.txt` | Dependencias Python del proyecto |
| `runtime.txt` | Versión de Python (3.11) |
| `package.json` | Dependencias Node/Playwright |
| `playwright.config.js` | Configuración de pruebas E2E |
| `.env.example` | Plantilla de variables de entorno |

### 16.2 Documentación Relacionada

| Recurso | URL |
|---------|-----|
| **Fuente de datos** | https://datosabiertos.bogota.gov.co/dataset/ips-servicios-cirugia-estetica |
| **Dash Documentation** | https://dash.plotly.com/ |
| **Plotly Python** | https://plotly.com/python/ |
| **Google Gemini API** | https://ai.google.dev/ |
| **Playwright** | https://playwright.dev/ |
| **Render** | https://render.com/docs |

### 16.3 Contacto del Proyecto

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

### Configuración de Asistente

```bash
# Copiar plantilla
copy .env.example .env

# Editar .env y agregar:
# GEMINI_API_KEY=tu_clave_aquí
```

### Despliegue

```bash
# Build command (Render)
pip install -r requirements.txt

# Start command (Render)
gunicorn run:server --bind 0.0.0.0:$PORT --workers 1 --timeout 120
```

---

*Documento generado para el Trabajo de Grado - Fundación Universitaria Compensar*
*Última actualización: Octubre 2026*
