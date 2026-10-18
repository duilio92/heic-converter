#!/usr/bin/env bash
set -e

echo "===================================================="
echo " Building HEIC Converter for Linux"
echo "===================================================="

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

if [ -f "venv/bin/python" ]; then
    PYTHON_BIN="venv/bin/python"
else
    PYTHON_BIN="python3"
fi

$PYTHON_BIN -m pip install -r requirements.txt
$PYTHON_BIN scripts/build.py

echo "Build complete. Output binary is in dist/heic-converter"
