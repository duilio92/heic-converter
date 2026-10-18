"""Data models and options for the HEIC converter."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class OutputFormat(str, Enum):
    """Supported target image formats."""
    JPEG = "JPEG"
    PNG = "PNG"
    WEBP = "WEBP"

    @property
    def extension(self) -> str:
        if self == OutputFormat.JPEG:
            return ".jpg"
        elif self == OutputFormat.PNG:
            return ".png"
        elif self == OutputFormat.WEBP:
            return ".webp"
        return ".jpg"


@dataclass
class ConversionOptions:
    """Configuration options for image conversion."""
    format: OutputFormat = OutputFormat.JPEG
    quality: int = 92
    keep_exif: bool = True
    auto_orient: bool = True
    output_dir: Optional[Path] = None
    overwrite: bool = False

    def __post_init__(self):
        # Validate quality range
        if not (1 <= self.quality <= 100):
            raise ValueError(f"Quality must be between 1 and 100, got {self.quality}")
        if self.output_dir is not None and not isinstance(self.output_dir, Path):
            self.output_dir = Path(self.output_dir)


@dataclass
class ConversionResult:
    """Outcome and metrics of a single file conversion."""
    input_path: Path
    output_path: Optional[Path]
    success: bool
    error_message: Optional[str] = None
    duration_seconds: float = 0.0
    original_size_bytes: int = 0
    converted_size_bytes: int = 0

    @property
    def size_change_ratio(self) -> float:
        if self.original_size_bytes > 0 and self.converted_size_bytes > 0:
            return self.converted_size_bytes / self.original_size_bytes
        return 0.0
