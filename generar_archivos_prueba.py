"""Script generador de carpetas y archivos de prueba para FilesPy.

Crea estructuras de carpetas con archivos variados para probar:
1. Renombrado por lotes (mayúsculas/minúsculas, prefijos, sufijos, secuenciales, regex).
2. Organización automática (por categoría, por extensión, por fecha YYYY/MM).
3. Detección de archivos duplicados (mismo contenido SHA-256 con distintos nombres).
4. Previsualización e inspección (imágenes reales con Pillow, código, texto, markdown).
5. Casos especiales (archivos sin extensión, archivos ignorados como .DS_Store y Thumbs.db).
"""
import io
import math
import os
from pathlib import Path
import struct
import tarfile
import time
import zipfile

from PIL import Image, ImageDraw


def create_image(path: Path, width: int, height: int, bg_color: tuple, text: str, shape: str = "rectangle"):
    """Genera una imagen real visible válida con Pillow."""
    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Dibujar formas decorativas
    if shape == "circle":
        draw.ellipse([20, 20, width - 20, height - 20], outline=(255, 255, 255), width=4)
    elif shape == "grid":
        for x in range(0, width, 40):
            draw.line([(x, 0), (x, height)], fill=(200, 200, 200, 50), width=1)
        for y in range(0, height, 40):
            draw.line([(0, y), (width, y)], fill=(200, 200, 200, 50), width=1)
    else:
        draw.rectangle([15, 15, width - 15, height - 15], outline=(255, 255, 255), width=3)

    # Intentar dibujar texto identificativo
    try:
        draw.text((30, height // 2 - 10), text, fill=(255, 255, 255))
    except Exception:
        pass

    path.parent.mkdir(parents=True, exist_ok=True)
    ext = path.suffix.lower()
    if ext in [".jpg", ".jpeg"]:
        img.save(path, format="JPEG", quality=90)
    elif ext == ".png":
        img.save(path, format="PNG")
    elif ext == ".bmp":
        img.save(path, format="BMP")
    elif ext == ".webp":
        img.save(path, format="WEBP")
    else:
        img.save(path)


def create_audio_wav(path: Path, freq: float = 440.0, duration: float = 0.5):
    """Genera un archivo de audio WAV sintético real válido."""
    path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 44100
    num_samples = int(sample_rate * duration)
    with open(path, "wb") as f:
        # Escribir encabezado RIFF/WAV manualmente o con wave
        import wave
        with wave.open(f, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            frames = bytearray()
            for i in range(num_samples):
                val = int(32767 * 0.4 * math.sin(2 * math.pi * freq * (i / sample_rate)))
                frames.extend(struct.pack("<h", val))
            wav.writeframes(frames)


def create_zip(path: Path, contents: dict):
    """Genera un archivo ZIP válido con archivos internos."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for fname, data in contents.items():
            z.writestr(fname, data)


def create_tar_gz(path: Path, contents: dict):
    """Genera un archivo TAR.GZ válido."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(path, "w:gz") as tar:
        for fname, data in contents.items():
            encoded = data.encode("utf-8")
            ti = tarfile.TarInfo(name=fname)
            ti.size = len(encoded)
            tar.addfile(ti, io.BytesIO(encoded))


def set_file_date(path: Path, year: int, month: int, day: int, hour: int = 12):
    """Ajusta la fecha de modificación mtime de un archivo."""
    dt = time.mktime((year, month, day, hour, 0, 0, 0, 0, -1))
    os.utime(path, (dt, dt))


def generate_all_test_folders(base_dir: Path):
    """Genera todas las carpetas y archivos de prueba en base_dir."""
    base_dir = Path(base_dir).resolve()
    base_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Generando archivos de prueba en: {base_dir}")

    # =========================================================================
    # 1. 01_para_organizar (Demostración de organización por categoría y extensión)
    # =========================================================================
    dir_org = base_dir / "01_para_organizar"
    dir_org.mkdir(exist_ok=True)

    # Documentos
    (dir_org / "informe_financiero_2026.pdf").write_bytes(
        b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
        b"xref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000115 00000 n \n"
        b"trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n185\n%%EOF\n"
    )
    (dir_org / "contrato_servicios_profesionales.docx").write_text(
        "Contrato de prestación de servicios profesionales - Versión Final 2026.", encoding="utf-8"
    )
    (dir_org / "presupuesto_anual_departamento.xlsx").write_text(
        "Presupuesto 2026\nDepartamento: TI\nTotal estimado: $50,000 USD", encoding="utf-8"
    )
    (dir_org / "notas_reunion_directiva.txt").write_text(
        "Notas de la reunión directiva del 28 de Octubre:\n- Aprobado plan de modernización.\n- Siguiente sprint comienza el lunes.",
        encoding="utf-8",
    )
    (dir_org / "lista_clientes_activos.csv").write_text(
        "id,nombre,email,pais,suscripcion\n1,Ana Lopez,ana@example.com,Mexico,Premium\n2,Carlos Diaz,carlos@example.com,Colombia,Basic\n3,Elena Ruiz,elena@example.com,Espana,Pro",
        encoding="utf-8",
    )

    # Imágenes
    create_image(dir_org / "banner_promocional_web.png", 640, 240, (244, 0, 72), "FilesPy Banner", "grid")
    create_image(dir_org / "avatar_usuario_admin.jpg", 320, 320, (30, 144, 255), "Avatar Admin", "circle")
    create_image(dir_org / "captura_grafico_ventas.webp", 480, 320, (46, 204, 113), "Ventas 2026", "rectangle")
    (dir_org / "icono_estrella_vectorial.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">'
        '<polygon points="50,5 64,36 98,36 70,57 81,91 50,70 19,91 30,57 2,36 36,36" fill="#f40048"/>'
        '</svg>',
        encoding="utf-8",
    )

    # Audio
    create_audio_wav(dir_org / "notificacion_campana.wav", freq=587.33, duration=0.8)
    (dir_org / "audio_podcast_episodio_01.mp3").write_bytes(
        b"ID3\x03\x00\x00\x00\x00\x00#" + b"\x00\xff\xfb\x90\x44" * 400
    )

    # Video
    (dir_org / "presentacion_producto_demo.mp4").write_bytes(
        b"\x00\x00\x00\x20ftypisom\x00\x00\x02\x00isomiso2mp41\x00\x00\x00\x08free" + b"\x00\x01\x02\x03" * 500
    )
    (dir_org / "grabacion_tutorial_flet.mkv").write_bytes(
        b"\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01\x42\xf7\x81\x01" + b"\x55\xaa\x33\xcc" * 400
    )

    # Comprimidos
    create_zip(
        dir_org / "paquete_recursos_graficos.zip",
        {"leame.txt": "Recursos gráficos oficiales de FilesPy.", "version.txt": "1.0.0"},
    )
    create_tar_gz(
        dir_org / "respaldo_base_datos.tar.gz",
        {"dump.sql": "CREATE TABLE usuarios (id INT, nombre VARCHAR(100));"},
    )

    # Código
    (dir_org / "algoritmo_clasificador.py").write_text(
        '"""Módulo de clasificación automatizada."""\n\ndef clasificar_dato(valor: float) -> str:\n    if valor > 100.0:\n        return "Alto"\n    elif valor > 50.0:\n        return "Medio"\n    return "Bajo"\n\nif __name__ == "__main__":\n    print(clasificar_dato(75.5))\n',
        encoding="utf-8",
    )
    (dir_org / "interfaz_interactiva.js").write_text(
        'document.addEventListener("DOMContentLoaded", () => {\n  console.log("FilesPy UI cargada exitosamente");\n  const btn = document.querySelector("#btn-accion");\n  if (btn) btn.onclick = () => alert("Acción ejecutada");\n});\n',
        encoding="utf-8",
    )
    (dir_org / "pagina_bienvenida.html").write_text(
        '<!DOCTYPE html>\n<html lang="es">\n<head>\n  <meta charset="UTF-8">\n  <title>Prueba FilesPy</title>\n</head>\n<body>\n  <h1>Bienvenido a FilesPy</h1>\n  <p>Archivo de prueba HTML para previsualización.</p>\n</body>\n</html>\n',
        encoding="utf-8",
    )
    (dir_org / "estilos_modo_oscuro.css").write_text(
        ':root {\n  --color-primary: #f40048;\n  --color-bg: #121212;\n  --color-surface: #1e1e1e;\n  --color-text: #ffffff;\n}\n\nbody {\n  background-color: var(--color-bg);\n  color: var(--color-text);\n  font-family: sans-serif;\n}\n',
        encoding="utf-8",
    )
    (dir_org / "parametros_servidor.json").write_text(
        '{\n  "app_name": "FilesPy Test",\n  "version": "1.0.0",\n  "debug": true,\n  "port": 8080,\n  "endpoints": [\n    "/api/status",\n    "/api/files",\n    "/api/organize"\n  ]\n}\n',
        encoding="utf-8",
    )

    # Formatos desconocidos (categoría 'Otros')
    (dir_org / "modelo_tensor_pesos.bin").write_bytes(b"\x00\xff\xee\xdd\xaa\x55" * 256)
    (dir_org / "exportacion_datos_crudos.xyz").write_text(
        "DATOS_XYZ_VALORES: 100, 200, 300, 400, 500", encoding="utf-8"
    )

    # Archivos sin extensión (categoría 'SIN_EXTENSION')
    (dir_org / "LEAME_INSTRUCCIONES").write_text(
        "Este archivo no posee extensión para probar la carpeta especial SIN_EXTENSION.",
        encoding="utf-8",
    )
    (dir_org / "LICENCIA_PROYECTO").write_text(
        "Licencia MIT - Archivo de texto plano sin extensión de archivo.",
        encoding="utf-8",
    )

    # Archivos ignorados por defecto en scanner
    (dir_org / ".DS_Store").write_bytes(b"\x00\x00\x00\x01Bud1\x00\x00\x10\x00")
    (dir_org / "Thumbs.db").write_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")

    # =========================================================================
    # 2. 02_para_renombrar (Pruebas de lote: mayúsculas, prefijos, números, etc.)
    # =========================================================================
    dir_ren = base_dir / "02_para_renombrar"
    dir_ren.mkdir(exist_ok=True)

    # Caso A: Fotos de cámara digital para numerar y agregar prefijo
    for i in range(1, 6):
        create_image(
            dir_ren / f"DSC_00{i:02d}_FOTO_VACACIONES.JPG",
            300, 200, (40 * i, 60, 180), f"Foto DSC {i}", "circle"
        )

    # Caso B: Archivos con nombres caóticos para normalizar (capitalización / snake_case)
    (dir_ren / "DOCUMENTO IMPORTANTE CON MAYUSCULAS Y ESPACIOS.pdf").write_text(
        "Texto de prueba para renombrar mayúsculas a snake_case o minusculas.", encoding="utf-8"
    )
    (dir_ren / "informe--borrador---version(1)--revisado.docx").write_text(
        "Borrador con guiones múltiples y paréntesis.", encoding="utf-8"
    )
    (dir_ren / "archivo-kebab-case-para-convertir.txt").write_text(
        "Contenido de prueba kebab-case.", encoding="utf-8"
    )
    (dir_ren / "mi_script_de_prueba_v1_backup_2025.py").write_text(
        "print('Script de prueba v1')\n", encoding="utf-8"
    )
    (dir_ren / "BALANCE_GENERAL_ANUAL_2024_PRELIMINAR.xlsx").write_text(
        "Balance general 2024", encoding="utf-8"
    )
    (dir_ren / "IMG_8941_CANON_RAW_SAMPLE.png").write_bytes(
        (dir_org / "banner_promocional_web.png").read_bytes()
    )

    # =========================================================================
    # 3. 03_para_duplicados (Pruebas de hash SHA-256 idéntico con nombres distintos)
    # =========================================================================
    dir_dup = base_dir / "03_para_duplicados"
    dir_dup.mkdir(exist_ok=True)

    # Grupo 1 de duplicados: Reporte Financiero (3 copias con nombres muy distintos)
    contenido_reporte = (
        "REPORTE EJECUTIVO ANUAL 2025\n"
        "============================\n"
        "Ingresos brutos: $1,250,000 MXN\n"
        "Costos operativos: $450,000 MXN\n"
        "Utilidad neta: $800,000 MXN\n"
        "Dictamen: Favorable sin salvedades.\n"
    ).encode("utf-8")

    (dir_dup / "reporte_ejecutivo_2025.txt").write_bytes(contenido_reporte)
    (dir_dup / "COPIA_SEGURIDAD_reporte_ejecutivo.txt").write_bytes(contenido_reporte)
    (dir_dup / "informe_2025_version_final_definitiva_ok.txt").write_bytes(contenido_reporte)

    # Grupo 2 de duplicados: Imagen con nombres diferentes
    img_dup_path1 = dir_dup / "fondo_pantalla_atardecer.png"
    create_image(img_dup_path1, 400, 300, (230, 80, 20), "Atardecer Duplicado", "circle")
    bytes_img = img_dup_path1.read_bytes()
    (dir_dup / "wallpaper_desktop_descargas.png").write_bytes(bytes_img)
    (dir_dup / "IMG_2026_ORIGINAL_BACKUP.png").write_bytes(bytes_img)

    # Grupo 3 de duplicados: Código Python idéntico
    contenido_script = (
        'import sys\n\ndef main():\n    print("Verificación de duplicados SHA-256")\n\n'
        'if __name__ == "__main__":\n    main()\n'
    ).encode("utf-8")
    (dir_dup / "script_limpieza.py").write_bytes(contenido_script)
    (dir_dup / "backup_script_limpieza_anterior.py").write_bytes(contenido_script)

    # Archivos ÚNICOS (sin duplicados) para verificar que no los agrupa
    (dir_dup / "archivo_exclusivo_unico_1.csv").write_text(
        "id,valor\n1,100\n2,200\n3,300\n", encoding="utf-8"
    )
    (dir_dup / "archivo_exclusivo_unico_2.md").write_text(
        "# Archivo Markdown Único\nEste archivo no tiene copias en el directorio.\n", encoding="utf-8"
    )
    create_image(dir_dup / "foto_exclusiva_no_duplicada.jpg", 300, 300, (80, 20, 150), "Foto Única", "rectangle")

    # =========================================================================
    # 4. 04_por_fechas (Pruebas de organización cronológica YYYY/MM)
    # =========================================================================
    dir_dates = base_dir / "04_por_fechas"
    dir_dates.mkdir(exist_ok=True)

    fechas_prueba = [
        ("factura_enero_2023.pdf", 2023, 1, 15, "Factura emitida en Enero 2023"),
        ("recibo_julio_2023.txt", 2023, 7, 20, "Recibo de servicios Julio 2023"),
        ("auditoria_marzo_2024.docx", 2024, 3, 10, "Auditoría interna Marzo 2024"),
        ("balance_diciembre_2024.xlsx", 2024, 12, 28, "Cierre de ejercicio Diciembre 2024"),
        ("presentacion_mayo_2025.pptx", 2025, 5, 14, "Presentación de resultados Mayo 2025"),
        ("contrato_septiembre_2025.pdf", 2025, 9, 22, "Contrato mercantil Septiembre 2025"),
        ("bitacora_enero_2026.log", 2026, 1, 8, "Registro de servidor Enero 2026"),
        ("reporte_octubre_2026.md", 2026, 10, 25, "Informe reciente Octubre 2026"),
    ]

    for fname, year, month, day, text in fechas_prueba:
        fpath = dir_dates / fname
        if fname.endswith(".pdf"):
            fpath.write_bytes(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n" + text.encode("utf-8"))
        elif fname.endswith((".docx", ".xlsx", ".pptx")):
            fpath.write_text(f"{fname}\n{text}\nFecha programada: {year}-{month:02d}-{day:02d}", encoding="utf-8")
        else:
            fpath.write_text(f"Contenido: {text}\nFecha: {year}-{month:02d}-{day:02d}\n", encoding="utf-8")
        set_file_date(fpath, year, month, day)

    # =========================================================================
    # 5. 05_carpeta_mixta_completa (Colección caótica para pruebas globales)
    # =========================================================================
    dir_mix = base_dir / "05_carpeta_mixta_completa"
    dir_mix.mkdir(exist_ok=True)

    # Copiar o generar un lote mixto de 20 archivos combinados
    (dir_mix / "DOCUMENTO_OFICIAL_2025.PDF").write_text("Documento oficial con mayúsculas", encoding="utf-8")
    (dir_mix / "balance_q1.csv").write_text("mes,ventas\n1,1000\n2,1200\n", encoding="utf-8")
    (dir_mix / "balance_q1_copia.csv").write_text("mes,ventas\n1,1000\n2,1200\n", encoding="utf-8")  # Duplicado
    (dir_mix / "notas_reunion.txt").write_text("Puntos clave de la reunión.", encoding="utf-8")
    (dir_mix / "IMG_0010_CAM.JPG").write_bytes((dir_ren / "DSC_0001_FOTO_VACACIONES.JPG").read_bytes())
    (dir_mix / "IMG_0011_CAM.JPG").write_bytes((dir_ren / "DSC_0002_FOTO_VACACIONES.JPG").read_bytes())
    (dir_mix / "logo_corporativo.png").write_bytes((dir_org / "banner_promocional_web.png").read_bytes())
    (dir_mix / "logo_corporativo_copia_descargas.png").write_bytes((dir_org / "banner_promocional_web.png").read_bytes())  # Duplicado
    (dir_mix / "script_migracion.py").write_text("print('Migración en progreso...')\n", encoding="utf-8")
    (dir_mix / "config.json").write_text('{"modo": "desarrollo", "activo": true}', encoding="utf-8")
    (dir_mix / "estilos.css").write_text("body { margin: 0; padding: 0; }", encoding="utf-8")
    (dir_mix / "archivo_sin_extension_info").write_text("Información sin extensión.", encoding="utf-8")
    (dir_mix / "musica_fondo.wav").write_bytes((dir_org / "notificacion_campana.wav").read_bytes())
    (dir_mix / "comprimido_adjunto.zip").write_bytes((dir_org / "paquete_recursos_graficos.zip").read_bytes())
    (dir_mix / "archivo_antiguo_2023.txt").write_text("Archivo antiguo de 2023", encoding="utf-8")
    set_file_date(dir_mix / "archivo_antiguo_2023.txt", 2023, 4, 12)
    (dir_mix / "archivo_medio_2024.txt").write_text("Archivo del 2024", encoding="utf-8")
    set_file_date(dir_mix / "archivo_medio_2024.txt", 2024, 8, 19)

    print("✅ Todas las carpetas y archivos de prueba fueron generados con éxito:")
    print(f"   1. {dir_org.name} ({len(list(dir_org.glob('*')))} archivos)")
    print(f"   2. {dir_ren.name} ({len(list(dir_ren.glob('*')))} archivos)")
    print(f"   3. {dir_dup.name} ({len(list(dir_dup.glob('*')))} archivos)")
    print(f"   4. {dir_dates.name} ({len(list(dir_dates.glob('*')))} archivos)")
    print(f"   5. {dir_mix.name} ({len(list(dir_mix.glob('*')))} archivos)")


if __name__ == "__main__":
    carpeta_destino = Path(__file__).parent / "archivos_prueba"
    generate_all_test_folders(carpeta_destino)
