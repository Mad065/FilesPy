#!/usr/bin/env bash
set -e

# ==============================================================================
# Script de Compilacion y Empaquetado para macOS (FilesPy)
# Genera FilesPy.app y FilesPy-macOS.dmg (instalador arrastrar-y-soltar)
# ==============================================================================

echo "==> Iniciando proceso de compilacion para macOS..."

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# 1. Asegurar iconos actualizados
python3 packaging/icon_generator.py

# 2. Instalar dependencias necesarias si pyinstaller no esta presente
if ! command -v pyinstaller &> /dev/null; then
    echo "==> Instalando PyInstaller..."
    python3 -m pip install --quiet pyinstaller
fi

# 3. Limpiar compilaciones previas
rm -rf build dist installer_output
mkdir -p installer_output

# 4. Ejecutar PyInstaller con la especificacion optimizada
echo "==> Compilando aplicacion con PyInstaller..."
pyinstaller packaging/FilesPy.spec --clean --noconfirm

# 5. Verificar creacion de FilesPy.app
if [ ! -d "dist/FilesPy.app" ]; then
    echo "ERROR: dist/FilesPy.app no fue generado."
    exit 1
fi

echo "==> FilesPy.app generado exitosamente en dist/FilesPy.app"

# 6. Crear DMG con acceso directo a /Applications para instalacion facil
echo "==> Generando instalador de disco macOS (.dmg)..."
DMG_STAGING="dist/dmg_staging"
rm -rf "$DMG_STAGING"
mkdir -p "$DMG_STAGING"

cp -R "dist/FilesPy.app" "$DMG_STAGING/"
ln -s /Applications "$DMG_STAGING/Applications"

hdiutil create -volname "FilesPy" \
    -srcfolder "$DMG_STAGING" \
    -ov -format UDZO \
    "installer_output/FilesPy-macOS.dmg"

# 7. Generar tambien archivo comprimido ZIP
cd dist
zip -r -q "../installer_output/FilesPy-macOS.zip" "FilesPy.app"
cd "$ROOT_DIR"

rm -rf "$DMG_STAGING"

echo ""
echo "=============================================================================="
echo "  COMPILACION COMPLETADA CON EXITO"
echo "  - Aplicacion: dist/FilesPy.app"
echo "  - Instalador DMG: installer_output/FilesPy-macOS.dmg"
echo "  - Archivo ZIP:    installer_output/FilesPy-macOS.zip"
echo "=============================================================================="
