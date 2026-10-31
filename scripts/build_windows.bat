@echo off
REM ==============================================================================
REM Script de Compilacion y Empaquetado para Windows (FilesPy)
REM Genera dist\FilesPy\FilesPy.exe y el instalador FilesPy-Windows-Setup.exe
REM ==============================================================================

echo [FilesPy] Iniciando compilacion para Windows...

cd /d "%~dp0\.."

REM 1. Generar iconos
python packaging\icon_generator.py

REM 2. Verificar dependencias
pip install -r requirements.txt pyinstaller --quiet

REM 3. Limpiar compilaciones anteriores
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist installer_output rmdir /s /q installer_output
mkdir installer_output

REM 4. Compilar con PyInstaller
echo [FilesPy] Compilando ejecutable con PyInstaller...
pyinstaller packaging\FilesPy.spec --clean --noconfirm

if not exist dist\FilesPy\FilesPy.exe (
    echo [ERROR] No se pudo generar dist\FilesPy\FilesPy.exe
    exit /b 1
)

REM 5. Generar archivo comprimido ZIP de distribucion portable
echo [FilesPy] Creando archivo portable ZIP...
powershell -Command "Compress-Archive -Path 'dist\FilesPy\*' -DestinationPath 'installer_output\FilesPy-Windows-x64.zip' -Force"

REM 6. Intentar compilar instalador con Inno Setup si esta disponible
set "ISCC_PATH="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC_PATH=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC_PATH=%ProgramFiles%\Inno Setup 6\ISCC.exe"

if defined ISCC_PATH (
    echo [FilesPy] Compilando instalador Setup con Inno Setup...
    "%ISCC_PATH%" packaging\inno_setup.iss
    echo [FilesPy] Instalador generado: installer_output\FilesPy-Windows-Setup.exe
) else (
    echo [FilesPy] Inno Setup no encontrado en el sistema. Se genero paquete ZIP portable en installer_output\FilesPy-Windows-x64.zip
)

echo.
echo ==============================================================================
echo   COMPILACION PARA WINDOWS COMPLETADA
echo   - Carpeta ejecutable: dist\FilesPy\
echo   - Paquete Portable:   installer_output\FilesPy-Windows-x64.zip
echo ==============================================================================
