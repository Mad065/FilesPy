#!/usr/bin/env python3
"""FilesPy - Organizador y Renombrador Inteligente de Archivos.

Aplicación de escritorio en Python y CustomTkinter para organizar y renombrar
archivos por lotes con vista previa interactiva, control de colisiones y deshacer.
"""
import sys
from ui.app import FilesPyApp


def main():
    try:
        app = FilesPyApp()
        app.mainloop()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
