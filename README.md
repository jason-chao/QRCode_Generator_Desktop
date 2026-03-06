# QR Code Generator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A clean cross-platform desktop application for generating QR codes, built with Python and Tkinter.

## Features

- Encode any URL or text into a QR code
- Customisable foreground and background colours (named colours, hex codes, or transparent)
- Visual colour picker with live swatch preview
- Adjustable error correction level (L / M / Q / H)
- Configurable box size (1–20 px) and quiet-zone border width
- Live preview with checkerboard display for transparent backgrounds
- Save as PNG, JPEG, BMP, GIF, TIFF, WebP, or ICO
- Persistent defaults via `config.ini`
- Packages into a standalone executable (no Python required at runtime)

## Requirements

- Python 3.10+
- Dependencies listed in `requirements.txt`:
  - `qrcode[pil]` >= 8.2
  - `Pillow` >= 12.1.1
  - `pyinstaller` >= 6.19.0 (build only)
- Test dependencies listed in `requirements-dev.txt`:
  - `pytest` >= 8.0

## Running from source

```bash
# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python qrcode_gen.py
```

## Running the tests

```bash
# Install dev dependencies (includes pytest)
pip install -r requirements-dev.txt

# Run all tests
pytest tests/
```

Tests cover all pure functions: `ec_label_for`, `is_valid_hex`, `normalise_colour`, `generate_qr_image`, and `load_config`. The Tkinter UI is not tested as it requires a display.

## Building a standalone executable

Build scripts handle virtual environment creation, dependency installation, and PyInstaller packaging automatically.

**Linux**
```bash
bash build_linux.sh
# Output: dist/QRCodeGen/QRCodeGen
```

**macOS**
```bash
bash build_macos.sh
# Output: dist/QRCodeGen.app  and  dist/QRCodeGen/QRCodeGen
```

**Windows**
```bat
build_windows.bat
REM Output: dist\QRCodeGen\QRCodeGen.exe
```

## Configuration

Default settings are stored in `config.ini` next to the executable. Edit it to change the startup defaults:

```ini
[defaults]
url              = https://example.com
foreground       = black
background       = transparent
error_correction = L   # L, M, Q, or H
box_size         = 10  # pixels per QR module (1–20)
border           = 2   # quiet-zone width in modules
```

## Project structure

```
qrcode-gen/
├── qrcode_gen.py          # Application source
├── qrcode_gen.spec        # PyInstaller spec (cross-platform)
├── config.ini             # Default settings
├── requirements.txt       # Runtime + build dependencies
├── requirements-dev.txt   # Dev/test dependencies
├── tests/
│   └── test_qrcode_gen.py # pytest test suite
├── build_linux.sh
├── build_macos.sh
└── build_windows.bat
```
