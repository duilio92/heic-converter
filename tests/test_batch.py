"""Tests for multithreaded batch conversion."""

import pytest
from pathlib import Path
from PIL import Image
import pillow_heif

from heic_converter.core.batch import BatchConverter
from heic_converter.core.models import ConversionOptions, OutputFormat

pillow_heif.register_heif_opener()


@pytest.fixture
def sample_batch(tmp_path: Path) -> list:
    files = []
    for i in range(5):
        img_path = tmp_path / f"batch_photo_{i}.heic"
        img = Image.new("RGB", (32, 32), color=(i * 40, 100, 100))
        img.save(img_path, format="HEIF")
        files.append(img_path)
    return files


def test_batch_convert_all_success(sample_batch: list, tmp_path: Path):
    out_dir = tmp_path / "batch_out"
    opts = ConversionOptions(format=OutputFormat.JPEG, output_dir=out_dir)

    progress_records = []

    def on_progress(done, total, res):
        progress_records.append((done, total, res.success))

    runner = BatchConverter(max_workers=2)
    summary = runner.convert_batch(sample_batch, options=opts, on_progress=on_progress)

    assert summary.total_files == 5
    assert summary.successful == 5
    assert summary.failed == 0
    assert summary.cancelled is False
    assert len(summary.results) == 5
    assert len(progress_records) == 5

    # Check that all 5 output files exist
    for f in sample_batch:
        expected_out = out_dir / f"{f.stem}.jpg"
        assert expected_out.exists()


def test_batch_convert_empty_list():
    runner = BatchConverter()
    summary = runner.convert_batch([])
    assert summary.total_files == 0
    assert summary.successful == 0
    assert summary.failed == 0
