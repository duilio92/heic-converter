"""Single-file conversion logic with EXIF and color management."""

import os
import time
from pathlib import Path
from typing import Optional
from PIL import Image, ImageOps
import pillow_heif

from heic_converter.core.models import ConversionOptions, ConversionResult, OutputFormat

# Register HEIF opener with Pillow on import
pillow_heif.register_heif_opener()


def resolve_output_path(input_path: Path, options: ConversionOptions) -> Path:
    """Calculates the target output path based on input path and options."""
    target_dir = options.output_dir if options.output_dir else input_path.parent
    extension = options.format.extension
    return target_dir / f"{input_path.stem}{extension}"


def convert_file(input_path: Path, options: Optional[ConversionOptions] = None) -> ConversionResult:
    """Converts a single HEIC/HEIF file to the target format.

    Args:
        input_path: Path to the source .heic or .heif file.
        options: Conversion configuration. Defaults to ConversionOptions() if None.

    Returns:
        ConversionResult containing outcome, timing, and size metrics.
    """
    if options is None:
        options = ConversionOptions()

    start_time = time.perf_counter()
    input_path = Path(input_path)

    if not input_path.is_file():
        return ConversionResult(
            input_path=input_path,
            output_path=None,
            success=False,
            error_message=f"Input file not found: {input_path}",
            duration_seconds=time.perf_counter() - start_time,
        )

    output_path = resolve_output_path(input_path, options)

    # Check if target file exists and overwrite is disabled
    if output_path.exists() and not options.overwrite:
        return ConversionResult(
            input_path=input_path,
            output_path=output_path,
            success=False,
            error_message=f"Destination file already exists (overwrite=False): {output_path}",
            duration_seconds=time.perf_counter() - start_time,
        )

    try:
        orig_size = input_path.stat().st_size

        with Image.open(input_path) as img:
            # 1. Correct physical orientation based on EXIF tag
            if options.auto_orient:
                img = ImageOps.exif_transpose(img)

            # 2. Extract EXIF metadata if requested
            exif_data = img.info.get("exif") if options.keep_exif else None

            # 3. Format and Color Profile Handling
            if options.format == OutputFormat.JPEG:
                # JPEG does not support transparency. If image has alpha channel, composite onto white background.
                if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                    alpha_img = img.convert("RGBA")
                    bg = Image.new("RGB", alpha_img.size, (255, 255, 255))
                    bg.paste(alpha_img, mask=alpha_img.split()[3])
                    target_img = bg
                elif img.mode != "RGB":
                    target_img = img.convert("RGB")
                else:
                    target_img = img

                # Ensure output directory exists
                output_path.parent.mkdir(parents=True, exist_ok=True)

                save_kwargs = {
                    "format": "JPEG",
                    "quality": options.quality,
                    "optimize": True,
                }
                if exif_data:
                    save_kwargs["exif"] = exif_data

                target_img.save(output_path, **save_kwargs)

            elif options.format == OutputFormat.PNG:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                save_kwargs = {
                    "format": "PNG",
                    "optimize": True,
                }
                if exif_data:
                    save_kwargs["exif"] = exif_data
                img.save(output_path, **save_kwargs)

            elif options.format == OutputFormat.WEBP:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                save_kwargs = {
                    "format": "WEBP",
                    "quality": options.quality,
                }
                if exif_data:
                    save_kwargs["exif"] = exif_data
                img.save(output_path, **save_kwargs)

        converted_size = output_path.stat().st_size
        duration = time.perf_counter() - start_time

        return ConversionResult(
            input_path=input_path,
            output_path=output_path,
            success=True,
            duration_seconds=duration,
            original_size_bytes=orig_size,
            converted_size_bytes=converted_size,
        )

    except Exception as e:
        duration = time.perf_counter() - start_time
        # Clean up partial output if failure occurred during write
        if output_path.exists():
            try:
                output_path.unlink()
            except OSError:
                pass

        return ConversionResult(
            input_path=input_path,
            output_path=output_path,
            success=False,
            error_message=str(e),
            duration_seconds=duration,
        )
