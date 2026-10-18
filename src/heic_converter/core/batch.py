"""Multithreaded batch conversion with progress tracking and cancellation."""

import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional

from heic_converter.core.models import ConversionOptions, ConversionResult
from heic_converter.core.converter import convert_file


@dataclass
class BatchSummary:
    """Aggregated metrics for a completed batch run."""
    total_files: int
    successful: int
    failed: int
    cancelled: bool
    total_duration_seconds: float
    total_original_bytes: int
    total_converted_bytes: int
    results: List[ConversionResult] = field(default_factory=list)

    @property
    def bytes_saved(self) -> int:
        return self.total_original_bytes - self.total_converted_bytes


class BatchConverter:
    """Manages multithreaded batch conversion of image files."""

    def __init__(self, max_workers: Optional[int] = None):
        # Default to CPU count (capped between 1 and 16)
        cpu_count = os.cpu_count() or 4
        self.max_workers = max_workers if max_workers else min(16, max(1, cpu_count))
        self._cancel_event = threading.Event()

    def cancel(self):
        """Requests cancellation of ongoing batch tasks."""
        self._cancel_event.set()

    def reset(self):
        """Resets the cancellation flag for a new run."""
        self._cancel_event.clear()

    def convert_batch(
        self,
        files: List[Path],
        options: Optional[ConversionOptions] = None,
        on_progress: Optional[Callable[[int, int, ConversionResult], None]] = None,
    ) -> BatchSummary:
        """Runs batch conversion over a list of file paths.

        Args:
            files: List of file paths to convert.
            options: Conversion settings.
            on_progress: Optional callback invoked as each file completes:
                         callback(completed_count, total_count, result).

        Returns:
            BatchSummary with aggregated results and timings.
        """
        self.reset()
        start_time = time.perf_counter()
        options = options or ConversionOptions()
        total_files = len(files)
        results: List[ConversionResult] = []

        if total_files == 0:
            return BatchSummary(
                total_files=0,
                successful=0,
                failed=0,
                cancelled=False,
                total_duration_seconds=0.0,
                total_original_bytes=0,
                total_converted_bytes=0,
                results=[],
            )

        completed_count = 0
        cancelled = False

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_path = {}
            for path in files:
                if self._cancel_event.is_set():
                    cancelled = True
                    break
                future = executor.submit(convert_file, path, options)
                future_to_path[future] = path

            for future in as_completed(future_to_path):
                path = future_to_path[future]
                if self._cancel_event.is_set():
                    cancelled = True

                try:
                    res = future.result()
                except Exception as e:
                    res = ConversionResult(
                        input_path=path,
                        output_path=None,
                        success=False,
                        error_message=str(e),
                    )

                results.append(res)
                completed_count += 1

                if on_progress:
                    on_progress(completed_count, total_files, res)

        duration = time.perf_counter() - start_time
        successful = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success)
        total_orig_bytes = sum(r.original_size_bytes for r in results)
        total_conv_bytes = sum(r.converted_size_bytes for r in results)

        return BatchSummary(
            total_files=total_files,
            successful=successful,
            failed=failed,
            cancelled=cancelled,
            total_duration_seconds=duration,
            total_original_bytes=total_orig_bytes,
            total_converted_bytes=total_conv_bytes,
            results=results,
        )
