# -*- mode: python ; coding: utf-8 -*-
# Receta de PyInstaller: arma un solo ControlDeHoras.exe sin consola.
import os

raiz = os.path.abspath(os.path.join(SPECPATH, ".."))

a = Analysis(
    [os.path.join(raiz, "app.py")],
    pathex=[raiz],
    binaries=[],
    datas=[],
    hiddenimports=["openpyxl", "reportlab", "reportlab.graphics.barcode"],
    hookspath=[],
    runtime_hooks=[],
    # Fuera lo que no usamos: el .exe baja de ~40 MB a ~15 MB.
    excludes=["numpy", "pandas", "matplotlib", "PIL", "scipy",
              "PyQt5", "PySide2", "IPython", "pytest"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name="ControlDeHoras",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,          # sin ventana negra detras
    icon=os.path.join(SPECPATH, "icono.ico"),
    version=os.path.join(SPECPATH, "version.txt"),
)
