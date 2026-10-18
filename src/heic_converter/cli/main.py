"""Command-line interface for HEIC converter."""

import argparse
import sys
from pathlib import Path
from typing import List, Set

from heic_converter.core.models import ConversionOptions, OutputFormat, ConversionResult
from heic_converter.core.batch import BatchConverter

SUPPORTED_EXTENSIONS: Set[str] = {".heic", ".heif"}


def find_heic_files(inputs: List[str], recursive: bool = False) -> List[Path]:
    """Collects HEIC/HEIF files from given file or directory paths."""
    collected: List[Path] = []
    seen: Set[Path] = set()

    for item in inputs:
        p = Path(item).resolve()
        if p.is_file():
            if p.suffix.lower() in SUPPORTED_EXTENSIONS and p not in seen:
                collected.append(p)
                seen.add(p)
        elif p.is_dir():
            pattern = "**/*" if recursive else "*"
            for candidate in p.glob(pattern):
                if (
                    candidate.is_file()
                    and candidate.suffix.lower() in SUPPORTED_EXTENSIONS
                    and candidate not in seen
                ):
                    collected.append(candidate)
                    seen.add(candidate)

    return sorted(collected)


def format_bytes(bytes_num: int) -> str:
    """Human-readable byte formatting."""
    for unit in ["B", "KB", "MB", "GB"]:
        if abs(bytes_num) < 1024.0:
            return f"{bytes_num:3.1f} {unit}"
        bytes_num /= 1024.0
    return f"{bytes_num:.1f} TB"


def cli_main(args=None) -> int:
    """Entry point for the CLI application."""
    parser = argparse.ArgumentParser(
        description="Convert HEIC/HEIF images to JPEG, PNG, or WEBP (Windows 10 & Linux compatible)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        help="One or more HEIC files, directories, or globs to convert.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default=None,
        help="Destination directory for converted files (defaults to same folder as original).",
    )
    parser.add_argument(
        "-q",
        "--quality",
        type=int,
        default=92,
        help="Image quality for JPEG/WEBP (1 to 100).",
    )
    parser.add_argument(
        "-f",
        "--format",
        type=str,
        default="JPEG",
        choices=["jpeg", "jpg", "png", "webp", "JPEG", "PNG", "WEBP"],
        help="Target image format.",
    )
    parser.add_argument(
        "--no-exif",
        action="store_true",
        help="Strip EXIF metadata (GPS, camera info, timestamp).",
    )
    parser.add_argument(
        "--no-auto-orient",
        action="store_true",
        help="Disable automatic EXIF orientation correction.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite destination files if they already exist.",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Recursively scan subdirectories for HEIC files.",
    )
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=None,
        help="Number of concurrent worker threads (defaults to CPU core count).",
    )

    parsed = parser.parse_args(args)

    # Resolve output format
    fmt_str = parsed.format.upper()
    if fmt_str in ("JPG", "JPEG"):
        output_format = OutputFormat.JPEG
    elif fmt_str == "PNG":
        output_format = OutputFormat.PNG
    elif fmt_str == "WEBP":
        output_format = OutputFormat.WEBP
    else:
        output_format = OutputFormat.JPEG

    output_dir = Path(parsed.output_dir).resolve() if parsed.output_dir else None

    # Discover files
    files = find_heic_files(parsed.inputs, recursive=parsed.recursive)
    if not files:
        print("No HEIC/HEIF files found in the specified path(s).", file=sys.stderr)
        return 1

    print(f"\nFound {len(files)} file(s) to convert.")
    print(f"Format: {output_format.value} | Quality: {parsed.quality}% | Keep EXIF: {not parsed.no_exif}")
    if output_dir:
        print(f"Output Directory: {output_dir}")
    print("-" * 60)

    options = ConversionOptions(
        format=output_format,
        quality=parsed.quality,
        keep_exif=not parsed.no_exif,
        auto_orient=not parsed.no_auto_orient,
        output_dir=output_dir,
        overwrite=parsed.overwrite,
    )

    def on_progress(done: int, total: int, res: ConversionResult):
        percent = int((done / total) * 100)
        status_symbol = "✓" if res.success else "✗"
        fname = res.input_path.name
        if res.success:
            print(f"[{done:>{len(str(total))}}/{total}] {percent:>3}% {status_symbol} {fname} ({res.duration_seconds:.2f}s)")
        else:
            print(f"[{done:>{len(str(total))}}/{total}] {percent:>3}% {status_symbol} {fname} -> FAILED: {res.error_message}")

    runner = BatchConverter(max_workers=parsed.workers)
    summary = runner.convert_batch(files, options=options, on_progress=on_progress)

    print("-" * 60)
    print("CONVERSION SUMMARY:")
    print(f"  Total Processed : {summary.total_files}")
    print(f"  Successful      : {summary.successful}")
    print(f"  Failed          : {summary.failed}")
    print(f"  Total Time      : {summary.total_duration_seconds:.2f}s")
    if summary.total_files > 0:
        avg = summary.total_duration_seconds / summary.total_files
        print(f"  Average / File  : {avg:.2f}s")
    if summary.total_original_bytes > 0:
        print(f"  Original Size   : {format_bytes(summary.total_original_bytes)}")
        print(f"  Output Size     : {format_bytes(summary.total_converted_bytes)}")
    print("-" * 60 + "\n")

    return 0 if summary.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(cli_main())
