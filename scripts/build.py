"""Cross-platform PyInstaller build script for HEIC Converter.

Creates a standalone executable on Windows (.exe) and Linux.
Ensures CustomTkinter theme assets and Pillow-HEIF binaries are bundled.
"""

import os
import platform
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def build():
    print(f"=== Building HEIC Converter on {platform.system()} ({platform.machine()}) ===")
    os.chdir(PROJECT_ROOT)

    output_name = "HEIC_Converter" if platform.system() == "Windows" else "heic-converter"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name",
        output_name,
        "--onefile",
        "--clean",
        # Ensure CustomTkinter assets, themes, and fonts are included
        "--collect-all",
        "customtkinter",
        # Ensure pillow_heif native binaries (.so / .dll) are included
        "--collect-all",
        "pillow_heif",
        # Paths
        "--paths",
        str(PROJECT_ROOT / "src"),
        str(PROJECT_ROOT / "main.py"),
    ]

    # If building on Windows or GUI wanted without terminal window popping up:
    # Note: On Windows, use --noconsole to suppress the command prompt window for the GUI
    if platform.system() == "Windows":
        cmd.append("--noconsole")

    print("Running command:")
    print(" ".join(cmd))
    print("-" * 60)

    result = subprocess.run(cmd)

    if result.returncode == 0:
        dist_dir = PROJECT_ROOT / "dist"
        binary_name = f"{output_name}.exe" if platform.system() == "Windows" else output_name
        binary_path = dist_dir / binary_name
        print("-" * 60)
        print(f"BUILD SUCCESSFUL!")
        print(f"Standalone executable generated at:")
        print(f"  {binary_path}")
        print("-" * 60)
    else:
        print(f"Build failed with exit code {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)


if __name__ == "__main__":
    build()
