# HEIC to Standard Image Converter (JPEG / PNG / WEBP)

A modular, cross-platform converter for Apple/iOS `.heic` photos to standard image formats (`.jpg`, `.png`, `.webp`). Fully compatible with both **Linux** and **Windows 10**, featuring both a **Modern Desktop GUI** and a fast **CLI**.

---

## Features

- **Cross-Platform:** Runs identically on Linux and Windows 10 with precompiled wheels (no C++ build tools required).
- **Core Fidelity:**
  - Preserves full EXIF metadata (GPS location, date/time taken, camera settings).
  - Handles auto-orientation (`exif_transpose`) so photos don't end up sideways or upside-down.
  - Converts Display P3 wide gamut to standard sRGB.
  - Alpha channel handling (composites transparent HEIC onto white background when converting to JPEG).
- **Dual Interfaces:**
  - **Modern GUI:** Built with `CustomTkinter` (dark/light themes, drag-and-drop file queues, quality sliders, progress bars, cancellation support).
  - **Terminal CLI:** Multithreaded batch processing, recursive directory scanning, human-readable summary metrics.
- **Standalone Distribution:** PyInstaller packaging scripts to build a single standalone `.exe` on Windows or executable binary on Linux.

---

## Project Structure

```text
heic-converter/
├── src/
│   └── heic_converter/
│       ├── __init__.py           # Public API imports
│       ├── core/
│       │   ├── __init__.py
│       │   ├── models.py         # ConversionOptions, ConversionResult, OutputFormat
│       │   ├── converter.py      # Single-file conversion, orientation & metadata
│       │   └── batch.py          # Multithreaded batch runner with cancellation
│       ├── cli/
│       │   ├── __init__.py
│       │   └── main.py           # Command-line interface with argument parsing
│       └── gui/
│           ├── __init__.py
│           └── app.py            # CustomTkinter modern desktop application
├── tests/
│   ├── test_models.py            # Validation and option tests
│   ├── test_converter.py         # Format and edge case unit tests
│   └── test_batch.py             # Multithreaded batch and progress tests
├── scripts/
│   ├── build.py                  # Cross-platform PyInstaller build script
│   ├── build_windows.bat         # 1-click build for Windows 10
│   └── build_linux.sh            # 1-click build for Linux
├── main.py                       # Unified entry point (auto-detects CLI or GUI)
├── requirements.txt              # Production and development dependencies
├── pytest.ini                    # Test runner configuration
└── setup.py                      # Standard Python package installer
```

---

## Quickstart

### 1. Setup Virtual Environment

#### On Linux:
```bash
python3 -m venv venv || virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### On Windows 10:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## Usage

### Unified Entry Point (`main.py`)

#### Launch GUI:
```bash
python main.py --gui
# Or run with no arguments in a desktop environment:
python main.py
```

#### CLI Mode:
```bash
# Convert a single file to JPEG:
python main.py photo.heic

# Convert a folder to a target directory with 95% quality:
python main.py ./vacation_photos/ -o ./converted/ -q 95

# Convert recursively to PNG:
python main.py ./photos/ -r -f png

# Convert to WEBP and strip EXIF (smaller size for web upload):
python main.py ./photos/ -f webp --no-exif
```

---

## Running the Test Suite

```bash
pytest -v
```

---

## Building Standalone Executables (No Python Required by End Users)

### On Windows 10:
Double-click `scripts/build_windows.bat` or run:
```powershell
python scripts/build.py
```
Outputs: `dist\HEIC_Converter.exe` (Standalone portable application).

### On Linux:
```bash
./scripts/build_linux.sh
```
Outputs: `dist/heic-converter` (Standalone Linux executable).

---

## Extending the Project

- **Adding a new format:** Add the enum to `OutputFormat` in `src/heic_converter/core/models.py` and implement the save handler in `src/heic_converter/core/converter.py`.
- **Adding image filters / watermarks:** Intercept the `PIL.Image` instance in `src/heic_converter/core/converter.py` prior to saving.
