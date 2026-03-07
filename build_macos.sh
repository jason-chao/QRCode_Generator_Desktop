#!/usr/bin/env bash
# Build script for macOS
# Run from the project root directory.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR=".venv"

echo "=== Good QR Code Generator — macOS build ==="

# 1. Create / reuse virtual environment
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

# 2. Install / upgrade dependencies
echo "Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# 3. Build with PyInstaller (produces a single-file exe and a .app bundle)
echo "Running PyInstaller..."
pyinstaller qrcode_gen.spec --clean --noconfirm

# 4. Place config.ini next to the executable so users can edit defaults
cp config.ini dist/
cp config.ini "dist/GoodQRCodeGen.app/Contents/MacOS/"

echo ""
echo "Build complete."
echo "  Single exe : dist/GoodQRCodeGen"
echo "  App bundle : dist/GoodQRCodeGen.app"
echo "  Config     : dist/config.ini  (edit to change defaults)"
