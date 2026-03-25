# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec file for Good QR Code Generator
#
# Produces a single-file executable on all platforms.
# config.ini is NOT bundled inside the exe; distribute it alongside the
# executable so users can edit their defaults.
#
# Usage (run from project root with venv active):
#   pyinstaller qrcode_gen.spec

import sys

block_cipher = None

a = Analysis(
    ["qrcode_gen.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("assets/icon.png", "assets"),   # window icon — Linux / macOS (iconphoto)
        ("assets/icon.ico", "assets"),   # window icon — Windows     (iconbitmap)
    ],
    hiddenimports=[
        "PIL._tkinter_finder",
        "qrcode.image.pil",
        "qrcode.image.styledpil",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    exclude_binaries=False,                     # onefile: embed everything into the exe
    name="GoodQRCodeGen",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,              # No console window on Windows / macOS
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/icon.ico",
)

# macOS: wrap the onefile exe in a .app bundle
if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="GoodQRCodeGen.app",
        icon="assets/icon.icns",
        bundle_identifier="com.example.qrcodegen",
        info_plist={
            "NSHighResolutionCapable": True,
            "CFBundleShortVersionString": "1.0.0",
        },
    )
