#!/usr/bin/env bash
set -e

echo "======================================"
echo " Transparent Build Script"
echo "======================================"
echo "This script compiles the transparent Python source code in 'scripts/'"
echo "into the standalone macOS binaries found in 'bin/'."
echo ""

echo "[1/4] Setting up a temporary virtual environment..."
rm -rf build_venv
python3 -m venv build_venv
source build_venv/bin/activate

echo "[2/4] Installing dependencies..."
pip install pyinstaller curl-cffi==0.8.1b9 wasmtime numpy nodriver drissionpage setuptools macholib

echo "[3/4] Compiling binaries..."
cd scripts
pyinstaller --onefile --collect-all wasmtime --collect-all curl_cffi --add-data "dsk:dsk" ask_deepseek.py
pyinstaller --onefile sync_canvas.py

echo "[4/4] Moving binaries to bin/ directory..."
cp dist/ask_deepseek ../bin/
cp dist/sync_canvas ../bin/

echo "Cleaning up..."
cd ..
rm -rf build_venv scripts/build scripts/dist scripts/*.spec

echo "Done! The executables have been built from source."
