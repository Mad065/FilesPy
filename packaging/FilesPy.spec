# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller specification file for FilesPy across Windows, macOS, and Linux."""

import os
import sys

block_cipher = None
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(SPEC), "."))

# Assets and resources to bundle
datas = [
    (os.path.join(PROJECT_ROOT, "assets"), "assets"),
    (os.path.join(PROJECT_ROOT, "settings.json"), "."),
]

# Hidden imports required by dynamic Flet / PIL components
hiddenimports = [
    "flet",
    "PIL",
    "PIL.Image",
    "PIL.ImageDraw",
    "PIL.ImageOps",
    "core",
    "core.config_manager",
    "core.conflicts",
    "core.duplicates",
    "core.models",
    "core.organizer",
    "core.renamer",
    "core.scanner",
    "core.undo",
    "ui",
    "ui.app",
    "ui.theme",
    "ui.components",
    "ui.components.action_bar",
    "ui.components.folder_bar",
    "ui.components.preview_table",
    "ui.components.inspector_panel",
    "ui.components.rename_panel",
    "ui.components.organize_panel",
    "ui.components.duplicate_panel",
    "ui.components.settings_dialog",
    "ui.components.step_review_dialog",
    "ui.components.manual_organize_dialog",
]

# Select proper icon per operating system
if sys.platform == "win32":
    icon_path = os.path.join(PROJECT_ROOT, "assets", "icons", "app_icon.ico")
elif sys.platform == "darwin":
    icon_path = os.path.join(PROJECT_ROOT, "assets", "icons", "app_icon.icns")
else:
    icon_path = os.path.join(PROJECT_ROOT, "assets", "icons", "app_icon.png")

a = Analysis(
    [os.path.join(PROJECT_ROOT, "main.py")],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tests", "archivos_prueba", "unittest", "pytest"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="FilesPy",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path if os.path.exists(icon_path) else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="FilesPy",
)

# On macOS, create a standalone .app bundle
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="FilesPy.app",
        icon=icon_path if os.path.exists(icon_path) else None,
        bundle_identifier="com.filespy.app",
        info_plist={
            "CFBundleName": "FilesPy",
            "CFBundleDisplayName": "FilesPy",
            "CFBundleExecutable": "FilesPy",
            "CFBundlePackageType": "APPL",
            "CFBundleShortVersionString": "0.1.0",
            "CFBundleVersion": "0.1.0",
            "NSHighResolutionCapable": "True",
            "LSMinimumSystemVersion": "10.15.0",
        },
    )
