#!/usr/bin/env python3
"""FilesPy - Organizador y Renombrador Inteligente de Archivos (Flet).

Aplicacion de escritorio ultra minimalista en Python y Flet para organizar
y renombrar archivos por lotes con vista previa interactiva y deshacer.
"""
import flet as ft
from ui.app import FilesPyApp


def main(page: ft.Page):
    FilesPyApp(page)


if __name__ == "__main__":
    if hasattr(ft, "run"):
        ft.run(main)
    else:
        ft.app(target=main)
