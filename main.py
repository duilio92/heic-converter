#!/usr/bin/env python3
"""Unified entry point for HEIC Converter (CLI & GUI).

Usage:
    # Launch GUI:
    python main.py --gui
    # Or simply:
    python main.py   (launches GUI if arguments are omitted and display is available)

    # CLI Usage:
    python main.py photo.heic -o ./output/
    python main.py ./photos_folder/ -r -q 90 -f JPEG
"""

import sys
from pathlib import Path

# Add src to python path for direct script execution
src_path = Path(__file__).resolve().parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


def main():
    # If explicitly requested --gui or no arguments passed
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] in ("--gui", "-g")):
        try:
            from heic_converter.gui.app import main as gui_main
            gui_main()
            return
        except Exception as e:
            # Fall back to CLI help if GUI fails to initialize (e.g. headless environment)
            print(f"Note: Could not start GUI ({e}). Switching to CLI mode.\n")
            from heic_converter.cli.main import cli_main
            cli_main(["--help"])
            return

    # Filter out --gui flag if passed with other args
    cli_args = [arg for arg in sys.argv[1:] if arg not in ("--gui", "-g")]
    from heic_converter.cli.main import cli_main
    sys.exit(cli_main(cli_args))


if __name__ == "__main__":
    main()
