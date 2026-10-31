#!/usr/bin/env bash
set -e

# ==============================================================================
# Script de Compilacion y Empaquetado para Linux (FilesPy)
# Genera dist/FilesPy/ y paquete tar.gz con lanzador .desktop e icono
# ==============================================================================

echo "==> Iniciando proceso de compilacion para Linux..."

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# 1. Generar iconos
python3 packaging/icon_generator.py

# 2. Instalar dependencias si faltan
if ! command -v pyinstaller &> /dev/null; then
    echo "==> Instalando PyInstaller..."
    python3 -m pip install --quiet pyinstaller
fi

# 3. Limpiar compilaciones anteriores
rm -rf build dist installer_output
mkdir -p installer_output

# 4. Compilar con PyInstaller
echo "==> Compilando aplicacion con PyInstaller..."
pyinstaller packaging/FilesPy.spec --clean --noconfirm

if [ ! -f "dist/FilesPy/FilesPy" ]; then
    echo "ERROR: dist/FilesPy/FilesPy no fue generado."
    exit 1
fi

# 5. Agregar lanzador .desktop e icono a la distribucion
echo "==> Agregando lanzador .desktop e icono del sistema..."
cp packaging/FilesPy.desktop dist/FilesPy/
cp assets/icons/app_icon.png dist/FilesPy/filespy.png

# Crear script lanzador rapido
cat << 'EOF' > dist/FilesPy/install.sh
#!/usr/bin/env bash
set -e
TARGET_DIR="$HOME/.local/share/filespy"
mkdir -p "$TARGET_DIR" "$HOME/.local/bin" "$HOME/.local/share/applications" "$HOME/.local/share/icons/hicolor/512x512/apps"

cp -r ./* "$TARGET_DIR/"
ln -sf "$TARGET_DIR/FilesPy" "$HOME/.local/bin/filespy"
cp "$TARGET_DIR/filespy.png" "$HOME/.local/share/icons/hicolor/512x512/apps/filespy.png"

sed -i "s|Exec=FilesPy|Exec=$HOME/.local/bin/filespy|g" "$TARGET_DIR/FilesPy.desktop"
cp "$TARGET_DIR/FilesPy.desktop" "$HOME/.local/share/applications/filespy.desktop"

echo "FilesPy instalado exitosamente en $TARGET_DIR."
echo "Puedes ejecutarlo escribiendo 'filespy' en la terminal o desde el menu de aplicaciones."
EOF
chmod +x dist/FilesPy/install.sh

# 6. Crear archivo comprimido tar.gz
echo "==> Creando paquete distribuible FilesPy-Linux-x64.tar.gz..."
cd dist
tar -czf "../installer_output/FilesPy-Linux-x64.tar.gz" FilesPy
cd "$ROOT_DIR"

echo ""
echo "=============================================================================="
echo "  COMPILACION COMPLETADA CON EXITO"
echo "  - Directorio: dist/FilesPy/"
echo "  - Paquete:    installer_output/FilesPy-Linux-x64.tar.gz"
echo "=============================================================================="
