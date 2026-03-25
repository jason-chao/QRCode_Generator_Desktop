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
pip install --upgrade pip
pip install -r requirements.txt

# 3. Generate icon.icns from icon.png (required for the .app bundle)
if [ ! -f assets/icon.icns ]; then
    echo "Generating assets/icon.icns..."
    ICONSET=$(mktemp -d)
    for size in 16 32 64 128 256 512; do
        sips -z $size $size assets/icon.png --out "$ICONSET/icon_${size}x${size}.png"
        double=$((size * 2))
        sips -z $double $double assets/icon.png --out "$ICONSET/icon_${size}x${size}@2x.png"
    done
    # iconutil expects a directory named *.iconset
    ICONSET_NAMED="$(dirname "$ICONSET")/icon.iconset"
    mv "$ICONSET" "$ICONSET_NAMED"
    iconutil -c icns "$ICONSET_NAMED" -o assets/icon.icns
    rm -rf "$ICONSET_NAMED"
fi

# 4. Build with PyInstaller (produces a .app bundle)
echo "Running PyInstaller..."
pyinstaller qrcode_gen.spec --clean --noconfirm

# 5. Place config.ini inside the .app so users can edit defaults
cp config.ini "dist/GoodQRCodeGen.app/Contents/MacOS/"

echo ""
echo "Build complete."
echo "  App bundle : dist/GoodQRCodeGen.app"
echo "  Config     : dist/GoodQRCodeGen.app/Contents/MacOS/config.ini  (edit to change defaults)"
