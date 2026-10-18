"""Tests for data models and options."""

import pytest
from pathlib import Path
from heic_converter.core.models import ConversionOptions, OutputFormat, ConversionResult


def test_output_format_extensions():
    assert OutputFormat.JPEG.extension == ".jpg"
    assert OutputFormat.PNG.extension == ".png"
    assert OutputFormat.WEBP.extension == ".webp"


def test_conversion_options_defaults():
    opts = ConversionOptions()
    assert opts.format == OutputFormat.JPEG
    assert opts.quality == 92
    assert opts.keep_exif is True
    assert opts.auto_orient is True
    assert opts.output_dir is None
    assert opts.overwrite is False


def test_conversion_options_quality_validation():
    with pytest.raises(ValueError, match="Quality must be between 1 and 100"):
        ConversionOptions(quality=0)

    with pytest.raises(ValueError, match="Quality must be between 1 and 100"):
        ConversionOptions(quality=105)


def test_conversion_result_ratio():
    res = ConversionResult(
        input_path=Path("test.heic"),
        output_path=Path("test.jpg"),
        success=True,
        original_size_bytes=1000,
        converted_size_bytes=500,
    )
    assert res.size_change_ratio == 0.5
