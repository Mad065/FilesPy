# FilesPy

> Gestor, organizador y renombrador por lotes de archivos con vista previa interactiva, control de colisiones, historial de deshacer y detección de duplicados en Python.

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![GUI Framework](https://img.shields.io/badge/GUI-CustomTkinter-blueviolet.svg)](https://customtkinter.tomschimansky.com/)
[![Tests](https://img.shields.io/badge/tests-21%20passed-success.svg)](tests/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## Tabla de Contenidos

- [Descripcion](#descripcion)
- [Caracteristicas Principales](#caracteristicas-principales)
- [Arquitectura del Sistema](#arquitectura-del-sistema)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Requisitos Previos](#requisitos-previos)
- [Instalacion y Configuracion](#instalacion-y-configuracion)
- [Guia de Uso](#guia-de-uso)
- [Pruebas Automatizadas](#pruebas-automatizadas)
- [Licencia](#licencia)

---

## Descripcion

**FilesPy** es una herramienta de escritorio construida sobre **Python 3** y **CustomTkinter** disenada para resolver de forma segura y eficiente la administracion masiva de archivos. Permite ordenar colecciones de archivos en directorios clasificados, renombrar grandes volumenes bajo multiples reglas encadenadas y verificar cada operacion mediante una tabla interactiva en tiempo real antes de escribir cualquier cambio en el almacenamiento secundario.

El diseno prioriza la integridad de datos: ninguna operacion modifica archivos fisicos sin confirmacion previa, se detectan activamente posibles colisiones de nombres o rutas, y cada lote ejecutado puede revertirse con un solo clic gracias a un gestor de transacciones reversibles.

---

## Caracteristicas Principales

### 1. Renombrado por Lotes (Batch Rename Engine)
- **Reemplazo de Texto**: Busqueda simple o mediante expresiones regulares (`Regex`), con opcion de sensibilidad a mayusculas y minusculas.
- **Prefijos y Sufijos**: Insercion de texto al inicio o al final del nombre base, conservando intacta la extension.
- **Numeracion Secuencial**: Generacion automatica de indices (`_001`, `_002`, etc.) con control del valor inicial y cantidad de digitos de relleno con ceros.
- **Normalizacion de Capitalizacion**: Conversion instantanea entre `minusculas`, `MAYUSCULAS`, `Titulo`, `snake_case` y `kebab-case`.
- **Manejo de Extensiones**: Capacidad para preservar, estandarizar o modificar la extension de los archivos seleccionados.

### 2. Organizacion Automatica en Carpetas
- **Por Extension**: Distribuye archivos en subcarpetas con el nombre de su formato (`PDF/`, `JPG/`, `TXT/`).
- **Por Categorias Dinamicas**: Agrupa segun la tipologia (`Documentos`, `Imagenes`, `Audio`, `Video`, `Comprimidos`, `Codigo`, `Otros`), personalizable por el usuario.
- **Por Fecha de Modificacion**: Estructura cronologica por Ano y Mes (`YYYY/MM`) segun los metadatos del archivo en disco.

### 3. Vista Previa Interactiva y Deteccion de Conflictos
- **Comparativa en Tiempo Real**: Visualizacion simultanea del nombre original, nuevo nombre propuesto, carpeta de destino y tamano.
- **Seleccion Granular**: Casillas para activar o excluir archivos de forma individual o mediante selector maestro.
- **Prevencion de Colisiones**: Analisis preventivo que detecta y bloquea la ejecucion si dos archivos comparten el mismo destino o si ya existe un archivo con ese nombre en el disco.

### 4. Inspector de Archivos (Pillow)
- Miniaturas fluidas para imagenes (`PNG`, `JPG`, `WEBP`, `GIF`, `BMP`, `SVG`).
- Visualizador de fragmentos de codigo y texto plano para inspeccion rapida de contenido.
- Desglose tecnico de metadatos: ruta absoluta, peso en formato legible (`KB`, `MB`, `GB`) y fecha de modificacion.

### 5. Deteccion de Duplicados (Hash Criptografico SHA-256)
- Identificacion en dos fases: filtrado inicial por tamano exacto en bytes seguido del calculo de hash SHA-256 en bloques de 64 KB.
- Permite detectar duplicados incluso con nombres totalmente distintos.
- Opcion directa para aislar copias redundantes dentro de una carpeta dedicada (`_Duplicados`).

### 6. Sistema de Deshacer (Undo / Rollback)
- Registro de transacciones atómicas en memoria y archivo de registro.
- Capacidad de revertir cualquier cambio aplicado de inmediato, restaurando carpetas y nombres a su estado exacto previo.

### 7. Modulo de Configuracion Persistente
- Boton dedicado en la interfaz para acceder al panel modal de configuracion.
- Permite crear nuevas categorias de extensiones (por ejemplo, `Modelado 3D` con `.blend, .obj, .fbx`), modificar las existentes o eliminarlas.
- Lista editable de archivos y patrones a omitir durante el escaneo (`.DS_Store`, `node_modules`, `Thumbs.db`, etc.).
- Persistencia automatica en [`settings.json`](settings.json) con funcion de restauracion a valores predeterminados.

---

## Arquitectura del Sistema

```text
+-----------------------------------------------------------------+
|                       Interfaz de Usuario                       |
|                          (CustomTkinter)                        |
|                                                                 |
|   +---------------+  +-------------------+  +---------------+   |
|   |   FolderBar   |  |  SettingsDialog   |  |   ActionBar   |   |
|   +---------------+  +-------------------+  +---------------+   |
|   | Tab: Renombrar|  | PreviewTable      |  | FileInspector |   |
|   | Tab: Organizar|  | (Grid Reactivo)   |  | (Thumbnails)  |   |
|   | Tab: Duplicads|  +-------------------+  +---------------+   |
+-----------------------------------------------------------------+
                               |
                               v
+-----------------------------------------------------------------+
|                         Capa de Negocio                         |
|                                                                 |
|   [ConfigManager]  -->  Gestion de settings.json y categorias   |
|   [DirectoryScanner]->  Descubrimiento y filtrado de rutas      |
|   [RenamerEngine]  -->  Reglas de texto, numeracion y formato   |
|   [OrganizerEngine]-->  Distribucion por extension/categoria    |
|   [ConflictDetector]->  Validacion de colisiones y rutas        |
|   [DuplicateFinder]-->  Calculo de hashes SHA-256               |
|   [UndoManager]    -->  Transacciones atomicas y rollback       |
+-----------------------------------------------------------------+
                               |
                               v
+-----------------------------------------------------------------+
|                      Sistema de Archivos                        |
|              (Almacenamiento Local / Disco Duro)                |
+-----------------------------------------------------------------+
```

---

## Estructura del Proyecto

```
FilesPy/
├── main.py                      # Punto de entrada de la aplicacion
├── requirements.txt             # Dependencias del proyecto
├── settings.json                # Configuraciones persistentes del usuario
├── .gitignore                   # Exclusiones de Git
├── README.md                    # Documentacion tecnica
├── core/                        # Modulos de logica de negocio
│   ├── __init__.py
│   ├── config_manager.py        # Gestion y persistencia de configuracion JSON
│   ├── conflicts.py             # Deteccion de colisiones y validacion de rutas
│   ├── duplicates.py            # Localizacion de duplicados por hash SHA-256
│   ├── models.py                # Modelos de datos (dataclasses tipados)
│   ├── organizer.py             # Clasificacion por extension, categoria o fecha
│   ├── renamer.py               # Motor de transformaciones de nombres
│   ├── scanner.py               # Explorador de directorios con filtros
│   └── undo.py                  # Pila de transacciones y operaciones reversibles
├── ui/                          # Capa visual (CustomTkinter)
│   ├── __init__.py
│   ├── app.py                   # Ventana principal y pipeline reactivo
│   ├── theme.py                 # Constantes de diseno y formateadores
│   └── components/              # Componentes visuales desacoplados
│       ├── __init__.py
│       ├── action_bar.py        # Barra de botones de accion (Aplicar, Deshacer)
│       ├── duplicate_panel.py   # Panel de analisis y aislamiento de duplicados
│       ├── folder_bar.py        # Barra de ruta, subcarpetas y configuracion
│       ├── inspector_panel.py   # Panel lateral de miniaturas y metadatos
│       ├── organize_panel.py    # Formulario de modos de organizacion
│       ├── preview_table.py     # Tabla interactiva con verificacion visual
│       ├── rename_panel.py      # Formulario de reglas de renombrado
│       └── settings_dialog.py   # Modal de edicion de categorias y preferencias
└── tests/                       # Suite de pruebas automatizadas
    ├── __init__.py
    ├── test_config_manager.py   # Pruebas de persistencia y defaults
    ├── test_conflicts.py        # Pruebas de deteccion de colisiones
    ├── test_duplicates.py       # Pruebas de huellas digitales SHA-256
    ├── test_integration.py      # Pruebas end-to-end de pipeline y rollback
    ├── test_organizer.py        # Pruebas de distribucion por carpetas
    ├── test_renamer.py          # Pruebas de reglas de renombrado
    └── test_undo.py             # Pruebas de transacciones reversibles
```

---

## Requisitos Previos

- **Python 3.10 o superior** (probado y verificado en Python 3.10, 3.11, 3.12 y 3.15).
- Compatible con macOS, Linux y Windows.

---

## Instalacion y Configuracion

### 1. Clonar el repositorio
```bash
git clone https://github.com/Mad065/FilesPy.git
cd FilesPy
```

### 2. Crear y activar el entorno virtual
En macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

En Windows:
```cmd
python -m venv .venv
.venv\Scripts\activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

---

## Guia de Uso

### Ejecutar la aplicacion
Con el entorno virtual activado:
```bash
python main.py
```

### Flujo de Trabajo Estandar:
1. **Seleccionar Carpeta**: Pulsa en `Explorar...` para cargar el directorio con los archivos a procesar. Activa la casilla `Subcarpetas` si deseas un escaneo recursivo.
2. **Definir Reglas**:
   - Pestaña **Renombrar**: Configura prefijos, sufijos, reemplazos, numeracion secuencial o cambios de capitalizacion.
   - Pestaña **Organizar**: Selecciona si deseas clasificar por extension, categoria dinamica o fecha.
   - Pestaña **Duplicados**: Ejecuta el analisis por hash para detectar archivos identicos repetidos.
3. **Inspeccionar Cambios**: La tabla central actualizara inmediatamente la columna `Nuevo Nombre` y `Carpeta Destino`. Las filas se marcaran en color segun su estado (verde para cambios listos, rojo para conflictos de nombre).
4. **Previsualizar Contenido**: Haz clic sobre cualquier archivo de la tabla para ver su miniatura (imagenes) o extracto de texto en el panel lateral derecho.
5. **Aplicar**: Pulsa en `Aplicar Cambios` para ejecutar las operaciones en el disco.
6. **Deshacer**: Si deseas revertir las modificaciones realizadas, presiona `Deshacer` para restaurar todos los archivos a sus rutas y nombres originales.

---

## Pruebas Automatizadas

El proyecto incluye 21 pruebas unitarias y de integracion que validan cada componente critico en entornos temporales aislados:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

Cobertura de pruebas:
- Reglas de reemplazo simple, insensible a mayusculas y expresiones regulares.
- Formateo de prefijos, sufijos y secuencias numeradas con ceros a la izquierda.
- Validacion y prevencion de colisiones de nombres o rutas preexistentes.
- Deteccion confiable de duplicados por hash SHA-256.
- Clasificacion en carpetas por extension y por categorias personalizadas.
- Modulo de persistencia y normalizacion de extensiones (`settings.json`).
- Flujo completo de transacciones en disco y rollback seguro con `UndoManager`.

---

## Licencia

Distribuido bajo la Licencia MIT. Consulta el archivo `LICENSE` para mas detalles.
