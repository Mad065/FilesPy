#!/usr/bin/env python3
"""
Generador de archivos y carpetas de prueba para FilesPy.
Crea un conjunto completo y categorizado de datos de prueba para verificar
cada función de FilesPy (Renombrado, Organización, Duplicados, Inspector,
Conflictos, Revisión Paso a Paso, Organización Manual, Automatización y Filtros).
"""

import os
import time
import zipfile
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


ROOT_DIR = Path(__file__).resolve().parent.parent
BASE_TEST_DIR = ROOT_DIR / "archivos_de_prueba"


def set_file_date(path: Path, year: int, month: int, day: int = 15):
    """Ajusta la fecha de modificación de un archivo para pruebas de organización por fecha."""
    dt = datetime(year, month, day, 12, 0, 0)
    ts = dt.timestamp()
    os.utime(path, (ts, ts))


def create_sample_image(path: Path, width=300, height=200, bg_color=(244, 0, 72), label="FilesPy"):
    """Crea una imagen válida (PNG, JPG, BMP, GIF, WEBP) con Pillow."""
    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    # Borde interior
    draw.rectangle([8, 8, width - 8, height - 8], outline=(255, 255, 255), width=3)
    # Patrón decorativo
    draw.line([(8, 8), (width - 8, height - 8)], fill=(255, 255, 255, 128), width=2)
    draw.line([(8, height - 8), (width - 8, 8)], fill=(255, 255, 255, 128), width=2)
    # Círculo central
    cx, cy, r = width // 2, height // 2, 35
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(20, 20, 20), outline=(255, 255, 255), width=2)
    
    path.parent.mkdir(parents=True, exist_ok=True)
    fmt = path.suffix.lstrip(".").upper()
    if fmt == "JPG":
        fmt = "JPEG"
    try:
        img.save(path, format=fmt)
    except Exception:
        img.save(path)


def create_sample_zip(path: Path, files_dict: dict):
    """Crea un archivo ZIP válido con contenido simulado."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname, content in files_dict.items():
            zf.writestr(fname, content)


def create_dummy_binary(path: Path, size_bytes: int, header: bytes = b""):
    """Crea un archivo binario ficticio con encabezado opcional."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(header)
        remaining = size_bytes - len(header)
        if remaining > 0:
            f.write(b"\x00" * remaining)


def create_sample_pdf(path: Path, title: str):
    """Crea un PDF válido mínimo."""
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf_content = (
        f"%PDF-1.4\n"
        f"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        f"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        f"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >> endobj\n"
        f"4 0 obj << /Length 55 >> stream\n"
        f"BT /F1 24 Tf 100 700 Td ({title}) Tj ET\n"
        f"endstream\n"
        f"endobj\n"
        f"xref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000216 00000 n \n"
        f"trailer << /Size 5 /Root 1 0 R >>\nstartxref\n320\n%%EOF\n"
    )
    with open(path, "w", encoding="latin-1") as f:
        f.write(pdf_content)


def generate_all():
    """Genera toda la jerarquía de pruebas."""
    if BASE_TEST_DIR.exists():
        import shutil
        shutil.rmtree(BASE_TEST_DIR)

    BASE_TEST_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 Creando entorno de pruebas en: {BASE_TEST_DIR}")

    # =========================================================================
    # 01. RENOMBRADO POR LOTES
    # =========================================================================
    d01 = BASE_TEST_DIR / "01_renombrado_lotes"
    d01.mkdir(parents=True, exist_ok=True)

    # 1.1 Casos para Buscar y Reemplazar (Texto simple y Regex)
    (d01 / "BORRADOR_informe_financiero_2023.pdf").write_text("Informe financiero borrador 2023", encoding="utf-8")
    (d01 / "BORRADOR_balance_contable_2023.xlsx").write_text("Balance contable borrador 2023", encoding="utf-8")
    (d01 / "BORRADOR_acta_asamblea_2023.docx").write_text("Acta asamblea borrador 2023", encoding="utf-8")
    (d01 / "OLD_PHOTO_vacaciones_cancun_01.jpg").write_text("Foto simulada", encoding="utf-8")
    (d01 / "OLD_PHOTO_vacaciones_cancun_02.jpg").write_text("Foto simulada", encoding="utf-8")

    # 1.2 Casos para Casing (MAYÚSCULAS, minúsculas, snake_case, kebab-case, Título)
    (d01 / "DOCUMENTO TOTALMENTE EN MAYUSCULAS.PDF").write_text("Texto en mayúsculas", encoding="utf-8")
    (d01 / "archivo_con_guiones_bajos_para_kebab.txt").write_text("Ejemplo snake a kebab", encoding="utf-8")
    (d01 / "un-archivo-con-guiones-para-snake.py").write_text("# Ejemplo kebab a snake", encoding="utf-8")
    (d01 / "nombre desordenado con espacios y minusculas.docx").write_text("Ejemplo titulo", encoding="utf-8")

    # 1.3 Casos para Prefijos, Sufijos y Numeración Secuencial
    (d01 / "capitulo_intro.txt").write_text("Capitulo introductorio", encoding="utf-8")
    (d01 / "capitulo_desarrollo.txt").write_text("Capitulo de desarrollo", encoding="utf-8")
    (d01 / "capitulo_conclusion.txt").write_text("Capitulo final", encoding="utf-8")

    # 1.4 Casos para Cambio de Extensión
    (d01 / "registro_sistema.log").write_text("[INFO] Registro de eventos", encoding="utf-8")
    (d01 / "respaldo_datos.bak").write_text("Datos de respaldo", encoding="utf-8")

    # =========================================================================
    # 02. ORGANIZACIÓN POR EXTENSIÓN
    # =========================================================================
    d02 = BASE_TEST_DIR / "02_organizacion_extension"
    d02.mkdir(parents=True, exist_ok=True)

    create_sample_pdf(d02 / "manual_usuario.pdf", "Manual de Usuario")
    create_sample_pdf(d02 / "especificaciones_tecnicas.pdf", "Especificaciones")
    create_sample_image(d02 / "captura_pantalla.png", 200, 150, (30, 144, 255), "PNG")
    create_sample_image(d02 / "fotografia_perfil.jpg", 200, 150, (46, 204, 113), "JPG")
    (d02 / "lista_tareas.txt").write_text("1. Revisar correos\n2. Diseñar UI\n3. Exportar reporte", encoding="utf-8")
    (d02 / "notas_reunion.txt").write_text("Reunión mensual de equipo", encoding="utf-8")
    create_sample_zip(d02 / "paquete_recursos.zip", {"readme.txt": "Contenido del zip"})
    (d02 / "archivo_sin_extension_demo").write_text("Este archivo no tiene extensión", encoding="utf-8")

    # =========================================================================
    # 03. ORGANIZACIÓN POR CATEGORÍAS (Documentos, Imágenes, Audio, Video, etc.)
    # =========================================================================
    d03 = BASE_TEST_DIR / "03_organizacion_categoria"
    d03.mkdir(parents=True, exist_ok=True)

    # Documentos
    create_sample_pdf(d03 / "contrato_servicios.pdf", "Contrato")
    (d03 / "reporte_anual.docx").write_text("Reporte anual corporativo", encoding="utf-8")
    (d03 / "balance_general.xlsx").write_text("Cuenta,Debe,Haber", encoding="utf-8")
    (d03 / "presentacion_ejecutiva.pptx").write_text("Diapositivas de venta", encoding="utf-8")
    (d03 / "catalogo_precios.csv").write_text("id,producto,precio\n1,Widget,19.99\n", encoding="utf-8")

    # Imágenes (válidas con Pillow para que se vean en el visor)
    create_sample_image(d03 / "arte_conceptual.png", 240, 180, (230, 57, 70), "Arte")
    create_sample_image(d03 / "banner_promocional.jpg", 320, 160, (244, 162, 97), "Banner")
    create_sample_image(d03 / "icono_aplicacion.webp", 128, 128, (42, 157, 143), "Icono")
    create_sample_image(d03 / "avatar_usuario.bmp", 120, 120, (155, 89, 182), "Avatar")

    # Audio (archivos con cabeceras simuladas)
    create_dummy_binary(d03 / "cancion_tema.mp3", 4096, header=b"ID3\x03\x00\x00\x00")
    create_dummy_binary(d03 / "efecto_sonido.wav", 4096, header=b"RIFF....WAVEfmt ")
    create_dummy_binary(d03 / "podcast_episodio_01.ogg", 4096, header=b"OggS\x00\x02")

    # Video (archivos simulados)
    create_dummy_binary(d03 / "demo_producto.mp4", 8192, header=b"\x00\x00\x00\x20ftypisom")
    create_dummy_binary(d03 / "tutorial_grabado.mkv", 8192, header=b"\x1a\x45\xdf\xa3")

    # Comprimidos
    create_sample_zip(d03 / "backup_proyecto.zip", {"index.html": "<h1>Test</h1>"})
    create_dummy_binary(d03 / "archivos_antiguos.rar", 2048, header=b"Rar!\x1a\x07\x00")
    create_dummy_binary(d03 / "libreria_externa.7z", 2048, header=b"7z\xbc\xaf\x27\x1c")

    # Código
    (d03 / "script_limpieza.py").write_text("import os\nprint('Limpiando...')\n", encoding="utf-8")
    (d03 / "app_interfaz.js").write_text("console.log('FilesPy App cargada');\n", encoding="utf-8")
    (d03 / "index.html").write_text("<!DOCTYPE html><html><body><h1>Prueba</h1></body></html>", encoding="utf-8")
    (d03 / "estilos.css").write_text("body { background: #121212; color: #fff; }\n", encoding="utf-8")
    (d03 / "esquema_bd.sql").write_text("CREATE TABLE usuarios (id INT, nombre TEXT);\n", encoding="utf-8")

    # Otros (extensión desconocida que irá a 'Otros')
    (d03 / "archivo_desconocido.xyz").write_text("Formato propietario XYZ", encoding="utf-8")
    (d03 / "temp_cache.customext").write_text("Datos temporales", encoding="utf-8")

    # Sin Extensión (irá a 'SIN_EXTENSION')
    (d03 / "LEEME_PRIMERO").write_text("Instrucciones sin extension", encoding="utf-8")
    (d03 / "Dockerfile").write_text("FROM python:3.11-slim\nWORKDIR /app\n", encoding="utf-8")

    # =========================================================================
    # 04. ORGANIZACIÓN POR FECHAS (YYYY/MM)
    # =========================================================================
    d04 = BASE_TEST_DIR / "04_organizacion_fechas"
    d04.mkdir(parents=True, exist_ok=True)

    f_2022_05 = d04 / "factura_compra_2022_05.pdf"
    create_sample_pdf(f_2022_05, "Factura 2022-05")
    set_file_date(f_2022_05, 2022, 5, 10)

    f_2023_01 = d04 / "informe_inicio_ano_2023_01.docx"
    f_2023_01.write_text("Informe 2023-01", encoding="utf-8")
    set_file_date(f_2023_01, 2023, 1, 15)

    f_2023_11 = d04 / "cierre_fiscal_2023_11.xlsx"
    f_2023_11.write_text("Cierre 2023-11", encoding="utf-8")
    set_file_date(f_2023_11, 2023, 11, 30)

    f_2024_03 = d04 / "presentacion_q1_2024_03.pptx"
    f_2024_03.write_text("Presentacion Q1 2024", encoding="utf-8")
    set_file_date(f_2024_03, 2024, 3, 20)

    f_2024_08 = d04 / "foto_evento_verano_2024_08.jpg"
    create_sample_image(f_2024_08, 200, 150, (255, 195, 0), "Verano 2024")
    set_file_date(f_2024_08, 2024, 8, 5)

    f_2025_02 = d04 / "presupuesto_proyectado_2025_02.pdf"
    create_sample_pdf(f_2025_02, "Presupuesto 2025-02")
    set_file_date(f_2025_02, 2025, 2, 14)

    # =========================================================================
    # 05. DETECCIÓN DE DUPLICADOS (SHA-256)
    # =========================================================================
    d05 = BASE_TEST_DIR / "05_duplicados"
    d05.mkdir(parents=True, exist_ok=True)

    # Par 1 de duplicados idénticos con nombres diferentes
    contenido_doc_duplicado = ("Este es el contenido exacto de un documento confidencial.\n" * 50).encode("utf-8")
    (d05 / "documento_original.pdf").write_bytes(contenido_doc_duplicado)
    (d05 / "copia_de_documento_original.pdf").write_bytes(contenido_doc_duplicado)

    # Trío de duplicados idénticos (3 copias)
    contenido_imagen = ("IMAGEN_RAW_SIMULADA_BYTES_EXACTOS_PARA_HASH_SHA256\n" * 80).encode("utf-8")
    (d05 / "IMG_2024_001.jpg").write_bytes(contenido_imagen)
    (d05 / "IMG_2024_001_copia.jpg").write_bytes(contenido_imagen)
    (d05 / "foto_vacaciones_respaldo.jpg").write_bytes(contenido_imagen)

    # Par 2 de duplicados
    contenido_cancion = b"ID3_AUDIO_STREAM_IDENTICO_1234567890" * 100
    (d05 / "pista_musical_01.mp3").write_bytes(contenido_cancion)
    (d05 / "copia_pista_musical_01.mp3").write_bytes(contenido_cancion)

    # CASO ESPECIAL: Archivos del MISMO TAMAÑO exacto pero DISTINTO CONTENIDO (Distinto SHA-256)
    # Esto prueba que el buscador de duplicados no da falsos positivos por tamaño.
    (d05 / "archivo_1024_bytes_letra_A.txt").write_bytes(b"A" * 1024)
    (d05 / "archivo_1024_bytes_letra_B.txt").write_bytes(b"B" * 1024)

    # Archivo único (sin duplicados)
    (d05 / "archivo_unico_irrepetible.txt").write_text("Soy un archivo unico y no tengo copias.", encoding="utf-8")

    # =========================================================================
    # 06. DETECCIÓN DE CONFLICTOS Y COLISIONES
    # =========================================================================
    d06 = BASE_TEST_DIR / "06_conflictos_y_colisiones"
    d06.mkdir(parents=True, exist_ok=True)

    # Subcarpeta destino con archivo preexistente
    destino_existente = d06 / "CarpetaDestino"
    destino_existente.mkdir(parents=True, exist_ok=True)
    (destino_existente / "archivo_duplicado.txt").write_text("Ya existo en destino!", encoding="utf-8")

    # Archivo en raíz que al moverse a CarpetaDestino provocará CONFLICT_EXISTS
    (d06 / "archivo_duplicado.txt").write_text("Quiero moverme a CarpetaDestino pero colisiono", encoding="utf-8")

    # Archivos que al renombrarse colisionan entre sí en el lote (CONFLICT_NAME)
    # Por ejemplo, si una regla quita los números '01' y '02' del final:
    (d06 / "reporte_anual_01.pdf").write_text("Reporte 1", encoding="utf-8")
    (d06 / "reporte_anual_02.pdf").write_text("Reporte 2", encoding="utf-8")

    # Archivo sin conflicto normal
    (d06 / "reporte_valido_sin_problemas.pdf").write_text("Sin problemas", encoding="utf-8")

    # =========================================================================
    # 07. INSPECTOR Y PREVISUALIZACIÓN (Imágenes y Visor de Código/Texto)
    # =========================================================================
    d07 = BASE_TEST_DIR / "07_inspector_previsualizacion"
    d07.mkdir(parents=True, exist_ok=True)

    # Imágenes coloridas de diferentes formatos y proporciones para miniaturas Pillow
    create_sample_image(d07 / "foto_alta_definicion.png", 400, 300, (244, 0, 72), "FilesPy HD")
    create_sample_image(d07 / "paisaje_colores.jpg", 320, 240, (52, 152, 219), "Paisaje")
    create_sample_image(d07 / "icono_sistema.bmp", 128, 128, (46, 204, 113), "Icono")
    create_sample_image(d07 / "grafico_circular.gif", 180, 180, (241, 196, 15), "Grafico")
    create_sample_image(d07 / "banner_web.webp", 450, 150, (155, 89, 182), "WebP")

    # Archivos de código y texto para previsualizar contenido en el inspector
    (d07 / "algoritmo_busqueda.py").write_text(
        '"""Modulo de busqueda binaria en Python."""\n\n'
        'def binary_search(arr: list, target: int) -> int:\n'
        '    low, high = 0, len(arr) - 1\n'
        '    while low <= high:\n'
        '        mid = (low + high) // 2\n'
        '        if arr[mid] == target:\n'
        '            return mid\n'
        '        elif arr[mid] < target:\n'
        '            low = mid + 1\n'
        '        else:\n'
        '            high = mid - 1\n'
        '    return -1\n\n'
        'if __name__ == "__main__":\n'
        '    print("Resultado:", binary_search([1, 3, 5, 7, 9], 7))\n',
        encoding="utf-8"
    )

    (d07 / "configuracion_servidor.json").write_text(
        '{\n'
        '  "app_name": "FilesPy Demo",\n'
        '  "version": "1.0.0",\n'
        '  "port": 8080,\n'
        '  "debug": true,\n'
        '  "database": {\n'
        '    "host": "localhost",\n'
        '    "port": 5432,\n'
        '    "username": "admin",\n'
        '    "pool_size": 10\n'
        '  },\n'
        '  "features": ["rename", "organize", "duplicates", "preview"]\n'
        '}\n',
        encoding="utf-8"
    )

    (d07 / "documentacion.md").write_text(
        '# Documentación de FilesPy\n\n'
        'Bienvenido al visor de archivos interactivo.\n\n'
        '## Características\n'
        '- Vista previa instantánea\n'
        '- Renderizado de miniaturas para imágenes\n'
        '- Lectura de código con colores oscuros\n\n'
        '| Formato | Soporte |\n'
        '|---|---|\n'
        '| PNG, JPG, WEBP | Miniatura visual |\n'
        '| PY, JSON, MD, TXT | Visor de texto |\n',
        encoding="utf-8"
    )

    (d07 / "datos_metricas.csv").write_text(
        'mes,visitas,conversiones,ingresos\n'
        'Enero,12000,450,14500.50\n'
        'Febrero,13500,520,16200.00\n'
        'Marzo,15000,610,19800.75\n'
        'Abril,17200,740,23400.20\n',
        encoding="utf-8"
    )

    # =========================================================================
    # 08. REVISIÓN PASO A PASO (Modo Interactivo: Aplicar, Conservar, Papelera)
    # =========================================================================
    d08 = BASE_TEST_DIR / "08_revision_paso_a_paso"
    d08.mkdir(parents=True, exist_ok=True)

    create_sample_image(d08 / "captura_pantalla_error_01.png", 260, 180, (231, 76, 60), "Error 01")
    (d08 / "borrador_acuerdo_confidencial.docx").write_text("Acuerdo borrador", encoding="utf-8")
    (d08 / "archivo_basura_temporal.tmp").write_text("Datos temporales descartables", encoding="utf-8")
    (d08 / "script_antiguo_obsoleto.py").write_text("# Script de prueba obsoleto\npass\n", encoding="utf-8")
    create_sample_pdf(d08 / "factura_pendiente_aprobacion.pdf", "Factura Pendiente")

    # =========================================================================
    # 09. ORGANIZACIÓN MANUAL Y NOMBRADO HÍBRIDO
    # =========================================================================
    d09 = BASE_TEST_DIR / "09_organizacion_manual"
    d09.mkdir(parents=True, exist_ok=True)

    # Facturas
    create_sample_pdf(d09 / "factura_luz_cfe_marzo.pdf", "Factura Luz")
    create_sample_pdf(d09 / "factura_internet_fibra_abril.pdf", "Factura Internet")
    create_sample_pdf(d09 / "recibo_honorarios_arquitecto.pdf", "Recibo Honorarios")

    # Fotos familiares / eventos
    create_sample_image(d09 / "cumpleanos_mama_2024.jpg", 220, 160, (230, 126, 34), "Cumpleaños")
    create_sample_image(d09 / "viaje_playa_familia.png", 220, 160, (26, 188, 156), "Playa")
    create_sample_image(d09 / "concierto_rock_con_amigos.jpg", 220, 160, (142, 68, 173), "Concierto")

    # Trabajo y clientes
    (d09 / "propuesta_proyecto_cliente_acme.docx").write_text("Propuesta ACME 2024", encoding="utf-8")
    (d09 / "cotizacion_software_empresa_xyz.xlsx").write_text("Cotización Software XYZ", encoding="utf-8")

    # =========================================================================
    # 10. MONITOREO Y AUTOMATIZACIÓN (Carpeta Vigilada / Inbox)
    # =========================================================================
    d10 = BASE_TEST_DIR / "10_monitoreo_automatizacion"
    d10.mkdir(parents=True, exist_ok=True)

    create_sample_pdf(d10 / "documento_descargado_01.pdf", "Descarga 01")
    create_sample_pdf(d10 / "documento_descargado_02.pdf", "Descarga 02")
    create_sample_image(d10 / "captura_reciente.png", 200, 140, (52, 73, 94), "Descarga")
    (d10 / "nota_rapida.txt").write_text("Nota tomada al vuelo", encoding="utf-8")
    create_sample_zip(d10 / "adjunto_correo.zip", {"archivo.txt": "adjunto"})

    # =========================================================================
    # 11. ESCANEO, FILTROS Y EXCLUSIONES (Archivos ignorados y ocultos)
    # =========================================================================
    d11 = BASE_TEST_DIR / "11_escaneo_y_filtros"
    d11.mkdir(parents=True, exist_ok=True)

    # Archivo normal visible
    (d11 / "documento_normal_visible.txt").write_text("Este archivo debe aparecer siempre", encoding="utf-8")
    create_sample_image(d11 / "foto_normal_visible.jpg", 180, 120, (39, 174, 96), "Visible")

    # Archivos y carpetas que DEBEN ignorarse según settings.json
    (d11 / ".DS_Store").write_bytes(b"\x00\x00\x00\x01Bud1\x00")
    (d11 / "Thumbs.db").write_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")
    (d11 / "desktop.ini").write_text("[.ShellClassInfo]\nIconResource=icon.ico,0\n", encoding="utf-8")

    # Mock de node_modules
    dir_node_modules = d11 / "node_modules" / "express"
    dir_node_modules.mkdir(parents=True, exist_ok=True)
    (dir_node_modules / "package.json").write_text('{"name": "express"}', encoding="utf-8")

    # Mock de __pycache__
    dir_pycache = d11 / "__pycache__"
    dir_pycache.mkdir(parents=True, exist_ok=True)
    (dir_pycache / "modulo.cpython-311.pyc").write_bytes(b"\x00" * 32)

    # Archivo oculto para probar el checkbox "Incluir archivos ocultos"
    (d11 / ".archivo_oculto_config").write_text("SECRET_KEY=12345\n", encoding="utf-8")

    # =========================================================================
    # 00. TODO EN UNO (SANDBOX COMPLETO PARA PRUEBA RÁPIDA)
    # =========================================================================
    d00 = BASE_TEST_DIR / "00_todo_en_uno"
    d00.mkdir(parents=True, exist_ok=True)

    # Lote de archivos variados con nombres desordenados, duplicados, diferentes tipos y fechas
    # para probar TODO en una sola carpeta seleccionada en la aplicación:
    create_sample_pdf(d00 / "DOC_2023_borrador_contrato.pdf", "Contrato")
    create_sample_pdf(d00 / "DOC_2023_factura_servicio_01.pdf", "Factura 1")
    set_file_date(d00 / "DOC_2023_factura_servicio_01.pdf", 2023, 4, 12)

    (d00 / "DOC_2023_balance_general.xlsx").write_text("Datos Excel", encoding="utf-8")
    set_file_date(d00 / "DOC_2023_balance_general.xlsx", 2023, 9, 25)

    (d00 / "PRESENTACION_VENTAS_FINAL_V2_FINAL.pptx").write_text("Diapositivas", encoding="utf-8")
    set_file_date(d00 / "PRESENTACION_VENTAS_FINAL_V2_FINAL.pptx", 2024, 1, 10)

    # Imágenes válidas
    create_sample_image(d00 / "IMG_20240815_PLAYA_VACACIONES.PNG", 300, 200, (41, 128, 185), "Playa")
    create_sample_image(d00 / "foto_cumpleanos_desordenada.jpg", 250, 180, (230, 126, 34), "Cumpleaños")
    create_sample_image(d00 / "banner_promocion_tienda.webp", 300, 150, (39, 174, 96), "Banner WebP")

    # Duplicados exactos en el sandbox
    contenido_dup_sandbox = b"CONTENIDO_DUPLICADO_SANDBOX_SHA256_TEST" * 30
    (d00 / "documento_importante.txt").write_bytes(contenido_dup_sandbox)
    (d00 / "copia_de_documento_importante.txt").write_bytes(contenido_dup_sandbox)

    # Audio y Video
    create_dummy_binary(d00 / "cancion_favorita.mp3", 4096, header=b"ID3\x03\x00")
    create_dummy_binary(d00 / "clip_tutorial.mp4", 8192, header=b"\x00\x00\x00\x20ftypisom")

    # Comprimido
    create_sample_zip(d00 / "paquete_archivos.zip", {"nota.txt": "Hola"})

    # Código
    (d00 / "script_principal.py").write_text("#!/usr/bin/env python3\nprint('Hola FilesPy!')\n", encoding="utf-8")
    (d00 / "configuracion_app.json").write_text('{"modo": "oscuro", "accent": "#f40048"}\n', encoding="utf-8")

    # Sin extensión y Otros
    (d00 / "archivo_sin_extension_demo").write_text("Archivo plano sin extension", encoding="utf-8")
    (d00 / "datos_propietarios.xyz").write_text("Formato no catalogado", encoding="utf-8")

    # Archivo de sistema a ignorar
    (d00 / "Thumbs.db").write_bytes(b"\xd0\xcf\x11\xe0")

    # =========================================================================
    # GUÍA DE USO EN MARKDOWN DENTRO DE LA CARPETA DE PRUEBAS
    # =========================================================================
    guia_md = BASE_TEST_DIR / "README_PRUEBAS.md"
    guia_md.write_text(
        """# Guía de Pruebas Rápidas de FilesPy

Este directorio contiene un conjunto de carpetas y archivos diseñados específicamente para probar **todas las funciones** de FilesPy.

---

## Índice de Pruebas

| Carpeta | Función de FilesPy que prueba | Cómo probarla en la app |
|---|---|---|
| **`00_todo_en_uno/`** | **Prueba general completa** | Abre esta carpeta y prueba todas las pestañas sin cambiar de directorio. Contiene duplicados, imágenes, documentos, código, etc. |
| **`01_renombrado_lotes/`** | **Motor de Renombrado** | Pestaña **Renombrar**:<br>1. Buscar `BORRADOR` y reemplazar por `OFICIAL`.<br>2. Probar normalización a `snake_case`, `kebab-case` o `MAYÚSCULAS`.<br>3. Probar numeración secuencial (`_001`, `_002`).<br>4. Cambiar extensión a `.txt`. |
| **`02_organizacion_extension/`** | **Organizar por Extensión** | Pestaña **Organizar** > Modo **Por Extensión**.<br>Observa cómo distribuye en subcarpetas `PDF/`, `PNG/`, `JPG/`, `TXT/`, `ZIP/`, etc. |
| **`03_organizacion_categoria/`** | **Organizar por Categoría** | Pestaña **Organizar** > Modo **Por Categoría**.<br>Agrupa en `Documentos/`, `Imágenes/`, `Audio/`, `Video/`, `Comprimidos/`, `Código/`, `Otros/` y `SIN_EXTENSION/`. |
| **`04_organizacion_fechas/`** | **Organizar por Fecha (`YYYY/MM`)** | Pestaña **Organizar** > Modo **Por Fecha**.<br>Los archivos tienen metadatos de fechas entre 2022 y 2025. Se ordenarán automáticamente en subcarpetas `2022/05`, `2023/01`, `2024/08`, etc. |
| **`05_duplicados/`** | **Detección de Duplicados (SHA-256)** | Pestaña **Duplicados** > Clic en **Detectar Duplicados**.<br>Detectará 3 grupos de duplicados exactos. Nota que `archivo_1024_bytes_letra_A` y `B` tienen el mismo tamaño pero distinto hash, por lo que no se marcan como duplicados. |
| **`06_conflictos_y_colisiones/`** | **Control de Colisiones** | Prueba mover archivos a `CarpetaDestino` o aplicar un reemplazo que deje a dos archivos con el mismo nombre. Verás las alertas en rojo / amarillo de conflicto. |
| **`07_inspector_previsualizacion/`** | **Inspector y Miniaturas (Pillow)** | Haz clic en cada fila de la tabla para ver:<br>- Miniatura generada por Pillow (`PNG`, `JPG`, `BMP`, `GIF`, `WEBP`).<br>- Visor de texto/código con sintaxis para `.py`, `.json`, `.md`, `.csv`. |
| **`08_revision_paso_a_paso/`** | **Revisión Paso a Paso** | Clic en el botón **Revisión Paso a Paso** en la barra inferior.<br>Recorre archivo por archivo decidiendo: **Aplicar**, **Conservar Original** o **Mover a Papelera**. |
| **`09_organizacion_manual/`** | **Organización Manual** | Clic en **Organización Manual**.<br>Asigna destinos con un clic (`Facturas`, `Fotos/Familia`, `Trabajo`) y usa el nombrado híbrido (`⚡ Auto-nombrar` o `snake_case`). |
| **`10_monitoreo_automatizacion/`** | **Vigilancia de Carpetas** | Clic en el botón de **Automatización / Monitoreo**.<br>Configura esta carpeta como vigilada con una regla (ej. prefijo de fecha `YYYYMMDD_` o auto-clasificación). |
| **`11_escaneo_y_filtros/`** | **Filtros y Archivos Omitidos** | Observa que `Thumbs.db`, `.DS_Store` y la carpeta `node_modules` no aparecen en la lista. Prueba activar el checkbox **Incluir archivos ocultos** para ver `.archivo_oculto_config`. |

---

## 🔄 ¿Cómo reiniciar o regenerar las pruebas?

Si aplicaste cambios, renombraste o moviste archivos y quieres volver a tener el conjunto de pruebas limpio, ejecuta:

```bash
python scripts/generar_archivos_prueba.py
```
""",
        encoding="utf-8"
    )

    print(f"✅ Entorno de pruebas creado exitosamente con {len(list(BASE_TEST_DIR.rglob('*')))} elementos.")
    print(f"📖 Guía detallada en: {guia_md}")


if __name__ == "__main__":
    generate_all()
