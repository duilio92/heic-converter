"""Tests for core conversion logic."""

import pytest
from pathlib import Path
from PIL import Image
import pillow_heif

from heic_converter.core.converter import convert_file, resolve_output_path
from heic_converter.core.models import ConversionOptions, OutputFormat

# Register HEIF opener
pillow_heif.register_heif_opener()


@pytest.fixture
def sample_heic(tmp_path: Path) -> Path:
    """Creates a temporary valid .heic image file for testing."""
    img_path = tmp_path / "test_photo.heic"
    img = Image.new("RGB", (64, 64), color=(200, 50, 50))
    img.save(img_path, format="HEIF")
    return img_path


def test_resolve_output_path_default(sample_heic: Path):
    opts = ConversionOptions(format=OutputFormat.JPEG)
    out = resolve_output_path(sample_heic, opts)
    assert out == sample_heic.parent / "test_photo.jpg"


def test_resolve_output_path_custom_dir(sample_heic: Path, tmp_path: Path):
    custom_dir = tmp_path / "custom_export"
    opts = ConversionOptions(format=OutputFormat.PNG, output_dir=custom_dir)
    out = resolve_output_path(sample_heic, opts)
    assert out == custom_dir / "test_photo.png"


def test_convert_to_jpeg_success(sample_heic: Path, tmp_path: Path):
    out_dir = tmp_path / "output_jpg"
    opts = ConversionOptions(format=OutputFormat.JPEG, quality=85, output_dir=out_dir)

    res = convert_file(sample_heic, opts)

    assert res.success is True
    assert res.output_path is not None
    assert res.output_path.exists()
    assert res.output_path.suffix == ".jpg"
    assert res.original_size_bytes > 0
    assert res.converted_size_bytes > 0

    # Verify the created JPEG is valid and can be opened
    with Image.open(res.output_path) as out_img:
        assert out_img.format == "JPEG"
        assert out_img.size == (64, 64)


def test_convert_to_png_success(sample_heic: Path, tmp_path: Path):
    out_dir = tmp_path / "output_png"
    opts = ConversionOptions(format=OutputFormat.PNG, output_dir=out_dir)

    res = convert_file(sample_heic, opts)

    assert res.success is True
    assert res.output_path.exists()
    assert res.output_path.suffix == ".png"

    with Image.open(res.output_path) as out_img:
        assert out_img.format == "PNG"


def test_convert_to_webp_success(sample_heic: Path, tmp_path: Path):
    out_dir = tmp_path / "output_webp"
    opts = ConversionOptions(format=OutputFormat.WEBP, quality=80, output_dir=out_dir)

    res = convert_file(sample_heic, opts)

    assert res.success is True
    assert res.output_path.exists()
    assert res.output_path.suffix == ".webp"

    with Image.open(res.output_path) as out_img:
        assert out_img.format == "WEBP"


def test_convert_missing_file():
    non_existent = Path("/non/existent/path/image.heic")
    res = convert_file(non_existent)
    assert res.success is False
    assert "Input file not found" in res.error_message


def test_overwrite_protection(sample_heic: Path, tmp_path: Path):
    out_dir = tmp_path / "output_overwrite"
    opts_no_overwrite = ConversionOptions(output_dir=out_dir, overwrite=False)

    # First conversion creates the file
    res1 = convert_file(sample_heic, opts_no_overwrite)
    assert res1.success is True

    # Second conversion should fail because overwrite is False
    res2 = convert_file(sample_heic, opts_no_overwrite)
    assert res2.success is False
    assert "already exists" in res2.error_message

    # With overwrite=True, it succeeds
    opts_with_overwrite = ConversionOptions(output_dir=out_dir, overwrite=True)
    res3 = convert_file(sample_heic, opts_with_overwrite)
    assert res3.success is True
