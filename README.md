# FilesPy

> Gestor, organizador y renombrador por lotes de archivos con vista previa interactiva, control de colisiones, historial de deshacer y detección de duplicados en Python.

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![GUI Framework](https://img.shields.io/badge/GUI-Flet%20(Flutter)-f40048.svg)](https://flet.dev/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](#instaladores-y-descargas)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## Tabla de Contenidos

- [Descripcion](#descripcion)
- [Caracteristicas Principales](#caracteristicas-principales)
- [Arquitectura del Sistema](#arquitectura-del-sistema)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Instaladores y Descargas](#instaladores-y-descargas)
- [Requisitos Previos](#requisitos-previos)
- [Instalacion y Configuracion](#instalacion-y-configuracion)
- [Guia de Uso](#guia-de-uso)
- [Licencia](#licencia)

---

## Descripcion

**FilesPy** es una herramienta de escritorio moderna y minimalista construida sobre **Python 3** y **Flet** (Flutter engine para Python) con un diseno en modo oscuro y acentos en **`#f40048`**. Esta disenada para resolver de forma rapida, segura y elegante la administracion masiva de archivos. Permite ordenar colecciones de archivos en directorios clasificados, renombrar grandes volumenes bajo multiples reglas encadenadas y verificar cada operacion mediante una tabla interactiva en tiempo real antes de escribir cualquier cambio en el disco.

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

### 8. Revision Paso a Paso (Modo Interactivo)
- Recorrido archivo por archivo con vista previa visual (miniaturas y codigo) y metadatos tecnicos detallados.
- Decision individual para cada archivo: **Aplicar Accion** (renombrar o mover), **Conservar Original** (omitir cambio) o **Eliminar Archivo** (mover de forma segura y reversible a `_Papelera`).
- Control de navegacion *Anterior / Siguiente* y atajos para aplicar o conservar los archivos restantes en lote.
- Registro total en el motor de transacciones: todo descarte o cambio puede revertirse con el boton **Deshacer**.

### 9. Organización Manual Personalizada y Nombrado Híbrido
- **Definición Dinámica de Carpetas**: Configura una lista personalizada de carpetas de destino (`Facturas`, `Fotos/Familia`, `Trabajo`, etc.) tanto desde el panel de organización como al vuelo durante el recorrido con el botón `＋ Agregar Carpeta`.
- **Recorrido Guiado Archivo por Archivo**: Vista previa interactiva con miniaturas (Pillow) o fragmentos de texto, metadatos y asignación de destino con un solo clic.
- **Nombrado Híbrido**:
  - **Manual**: Edición libre en campo de texto con validación de nombres válidos.
  - **Automático**: Botones dedicados para aplicar reglas activas de renombrado (`⚡ Auto-nombrar`), normalización instantánea (`snake_case`) o restaurar el nombre original (`↺ Original`).
- **Clasificación Veloz (Auto-avance)**: Opción para avanzar inmediatamente al siguiente archivo tras seleccionar la carpeta de destino.
- **Totalmente Reversible**: Integración con `UndoManager` para deshacer todas las asignaciones y cambios aplicados con un clic.

---

## Arquitectura del Sistema

```text
+-----------------------------------------------------------------+
|                       Interfaz de Usuario                       |
|                       (Flet / Flutter Engine)                   |
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
├── assets/                      # Iconos y recursos graficos
│   └── icons/                   # Iconos vectoriales y ejecutables (.ico, .icns, .png)
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
├── ui/                          # Capa visual minimalista (Flet)
│   ├── __init__.py
│   ├── app.py                   # Ventana principal y pipeline reactivo
│   ├── theme.py                 # Constantes de diseno y formateadores
│   └── components/              # Componentes visuales desacoplados
│       ├── __init__.py
│       ├── action_bar.py        # Barra de botones de accion (Aplicar, Deshacer)
│       ├── duplicate_panel.py   # Panel de analisis y aislamiento de duplicados
│       ├── folder_bar.py        # Barra de ruta, subcarpetas y configuracion
│       ├── inspector_panel.py   # Panel lateral de miniaturas y metadatos
│       ├── manual_organize_dialog.py # Dialogo interactivo de clasificacion y nombrado hibrido
│       ├── organize_panel.py    # Formulario de modos de organizacion
│       ├── preview_table.py     # Tabla interactiva con verificacion visual
│       ├── rename_panel.py      # Formulario de reglas de renombrado
│       ├── settings_dialog.py   # Modal de edicion de categorias y preferencias
│       └── step_review_dialog.py # Revision paso a paso interactiva
├── packaging/                   # Archivos de configuracion de empaquetado
│   ├── FilesPy.spec             # Especificacion PyInstaller multiplataforma
│   ├── FilesPy.desktop          # Lanzador de escritorio para Linux
│   ├── inno_setup.iss           # Asistente instalador para Windows (Inno Setup)
│   └── icon_generator.py        # Utilidad generadora de iconos .ico/.icns/.png
└── scripts/                     # Scripts de compilacion local automatizada
    ├── build_macos.sh           # Generador de .app y .dmg para macOS
    ├── build_windows.bat        # Generador de .exe y Setup para Windows
    └── build_linux.sh           # Generador de .tar.gz y .desktop para Linux
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

## Instaladores y Descargas

FilesPy esta disponible como ejecutable e instalador independiente para **Windows**, **macOS** y **Linux**, sin necesidad de tener Python instalado.

### Descarga de Versiones Compiladas

| Sistema Operativo | Formato de Paquete | Descripcion |
| :--- | :--- | :--- |
| **Windows** (x64) | `FilesPy-Windows-Setup.exe` / `.zip` | Asistente de instalacion Inno Setup con accesos directos o version portable. |
| **macOS** (Intel / Apple Silicon) | `FilesPy-macOS.dmg` / `.zip` | Imagen de disco arrastrar-y-soltar lista para mover a `/Applications`. |
| **Linux** (x64) | `FilesPy-Linux-x64.tar.gz` | Paquete portable con instalador de acceso directo `.desktop` y lanzador `install.sh`. |

Puedes descargar los paquetes mas recientes desde la seccion de **[Releases de GitHub](https://github.com/Mad065/FilesPy/releases)**.

---

### Compilacion Local de Instaladores

Si deseas compilar los paquetes de instalacion por tu cuenta en tu sistema local:

#### En macOS:
```bash
chmod +x scripts/build_macos.sh
./scripts/build_macos.sh
```
*Genera:* `dist/FilesPy.app`, `installer_output/FilesPy-macOS.dmg` e `installer_output/FilesPy-macOS.zip`.

#### En Windows:
```cmd
scripts\build_windows.bat
```
*Genera:* `dist\FilesPy\FilesPy.exe`, `installer_output\FilesPy-Windows-x64.zip` y (si se dispone de Inno Setup) `installer_output\FilesPy-Windows-Setup.exe`.

#### En Linux:
```bash
chmod +x scripts/build_linux.sh
./scripts/build_linux.sh
```
*Genera:* `installer_output/FilesPy-Linux-x64.tar.gz` con el lanzador `install.sh`.

---

### Integracion Continua (CI/CD Automatizado)

El repositorio incluye un flujo automatizado en **GitHub Actions** (`.github/workflows/build-installers.yml`):
- Se activa automaticamente al publicar una etiqueta de version (`v*`) o mediante disparo manual (`workflow_dispatch`).
- Compila concurrentemente en maquinas virtuales nativas de Windows, macOS y Linux.
- Genera y adjunta todos los instaladores finales al Release de GitHub.

---

## Licencia

Distribuido bajo la Licencia MIT. Consulta el archivo `LICENSE` para mas detalles.
