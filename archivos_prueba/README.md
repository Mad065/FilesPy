# Archivos de Prueba para FilesPy

Este directorio contiene lotes de archivos creados específicamente para probar todas las funciones de **FilesPy** sin poner en riesgo archivos personales.

---

## Estructura de las Carpetas

### 📁 `01_para_organizar/`
Diseñada para probar la pestaña **Organizar**:
- **Por Categoría**:
  - `Documentos`: `.pdf`, `.docx`, `.xlsx`, `.txt`, `.csv`
  - `Imágenes`: `.png`, `.jpg`, `.webp`, `.svg` (las imágenes son archivos válidos visibles en el inspector)
  - `Audio`: `.mp3`, `.wav` (audio WAV sintético real)
  - `Video`: `.mp4`, `.mkv`
  - `Comprimidos`: `.zip`, `.tar.gz` (archivos comprimidos válidos)
  - `Código`: `.py`, `.js`, `.html`, `.css`, `.json`
  - `Otros`: `.bin`, `.xyz`
  - `SIN_EXTENSION`: archivos sin extensión (`LEAME_INSTRUCCIONES`, `LICENCIA_PROYECTO`)
- **Por Extensión**: Crea subcarpetas individuales en mayúsculas (`PDF/`, `PNG/`, `TXT/`, etc.).
- **Filtro de ignorados**: Incluye archivos de prueba `.DS_Store` y `Thumbs.db` para comprobar que el escáner los omite según la configuración.

---

### 📁 `02_para_renombrar/`
Diseñada para probar la pestaña **Renombrar**:
- **Numeración Secuencial**: Lote de fotos (`DSC_0001_FOTO_VACACIONES.JPG` a `DSC_0005...`) ideal para aplicar numeración `_001`, `_002`, etc.
- **Normalización de Texto**: Archivos con mayúsculas y espacios (`DOCUMENTO IMPORTANTE CON MAYUSCULAS Y ESPACIOS.pdf`) para probar `minúsculas`, `snake_case`, `kebab-case` o `Título`.
- **Búsqueda y Reemplazo**: Archivos con patrones repetitivos (`--borrador---version(1)--revisado`, `_backup_2025`, etc.) para probar reemplazo simple o Regex.
- **Prefijos y Sufijos**: Inserción de prefijos como `Proyecto_` o sufijos como `_v1`.

---

### 📁 `03_para_duplicados/`
Diseñada para probar la pestaña **Duplicados** (detección por hash SHA-256):
- **Grupo 1**: Reporte ejecutivo (`reporte_ejecutivo_2025.txt`, `COPIA_SEGURIDAD_reporte_ejecutivo.txt`, `informe_2025_version_final_definitiva_ok.txt`). Tres archivos con nombres totalmente distintos pero contenido y hash SHA-256 exactamente idénticos.
- **Grupo 2**: Fondos de pantalla duplicados (`fondo_pantalla_atardecer.png`, `wallpaper_desktop_descargas.png`, `IMG_2026_ORIGINAL_BACKUP.png`).
- **Grupo 3**: Scripts de Python idénticos (`script_limpieza.py` y `backup_script_limpieza_anterior.py`).
- **Archivos únicos**: Archivos sin copias para comprobar que el algoritmo no genera falsos positivos.

---

### 📁 `04_por_fechas/`
Diseñada para probar la organización cronológica (`YYYY/MM`):
- Archivos cuyas fechas de modificación (`mtime`) han sido calibradas con fechas específicas:
  - `2023/01` y `2023/07`
  - `2024/03` y `2024/12`
  - `2025/05` y `2025/09`
  - `2026/01` y `2026/10`

---

### 📁 `05_carpeta_mixta_completa/`
Simula una carpeta caótica del mundo real (similar a una carpeta de "Descargas"):
- Contiene una mezcla de imágenes, audios, documentos, código, duplicados y fechas variadas para probar todas las herramientas simultáneamente.

---

## 🔄 ¿Cómo reiniciar o regenerar los archivos de prueba?

Si ejecutas operaciones sobre estas carpetas y deseas restaurarlas a su estado original de prueba, simplemente corre el siguiente comando en la terminal:

```bash
python3 generar_archivos_prueba.py
```
