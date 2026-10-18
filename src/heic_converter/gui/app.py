"""Desktop graphical interface for HEIC converter using CustomTkinter."""

import os
import sys
import threading
from pathlib import Path
from typing import List, Optional

try:
    import customtkinter as ctk
    from tkinter import filedialog, messagebox
    HAS_GUI_DEPENDENCIES = True
except (ImportError, ModuleNotFoundError) as err:
    HAS_GUI_DEPENDENCIES = False
    GUI_IMPORT_ERROR = str(err)

from heic_converter.core.models import ConversionOptions, OutputFormat, ConversionResult
from heic_converter.core.batch import BatchConverter, BatchSummary


class HeicConverterApp:
    """Wrapper to initialize and run the CustomTkinter desktop interface."""

    def __init__(self):
        if not HAS_GUI_DEPENDENCIES:
            raise RuntimeError(
                f"GUI dependencies are not available ({GUI_IMPORT_ERROR}).\n"
                "On Ubuntu/Debian Linux: run 'sudo apt install python3-tk'.\n"
                "On Windows 10: Tkinter is included automatically with the standard Python installer."
            )

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("HEIC to Standard Image Converter (JPEG / PNG / WEBP)")
        self.root.geometry("640x620")
        self.root.minsize(580, 560)

        # State variables
        self.selected_files: List[Path] = []
        self.output_dir: Optional[Path] = None
        self.is_converting = False
        self.batch_runner = BatchConverter()

        self._build_ui()

    def _build_ui(self):
        # 1. Header Section
        self.header_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=24, pady=(18, 10))

        self.title_lbl = ctk.CTkLabel(
            self.header_frame,
            text="HEIC Converter",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        self.title_lbl.pack(anchor="w")

        self.subtitle_lbl = ctk.CTkLabel(
            self.header_frame,
            text="Convert iOS / camera HEIC photos to standard JPEG, PNG, or WEBP",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8",
        )
        self.subtitle_lbl.pack(anchor="w")

        # 2. File Selection Card
        self.file_card = ctk.CTkFrame(self.root, corner_radius=10)
        self.file_card.pack(fill="x", padx=24, pady=8)

        self.file_actions = ctk.CTkFrame(self.file_card, fg_color="transparent")
        self.file_actions.pack(fill="x", padx=14, pady=12)

        self.btn_select_files = ctk.CTkButton(
            self.file_actions,
            text="+ Add Files",
            width=110,
            command=self._on_select_files,
        )
        self.btn_select_files.pack(side="left", padx=(0, 8))

        self.btn_select_folder = ctk.CTkButton(
            self.file_actions,
            text="+ Add Folder",
            width=110,
            fg_color="#334155",
            hover_color="#475569",
            command=self._on_select_folder,
        )
        self.btn_select_folder.pack(side="left", padx=4)

        self.btn_clear_files = ctk.CTkButton(
            self.file_actions,
            text="Clear",
            width=70,
            fg_color="#7f1d1d",
            hover_color="#991b1b",
            command=self._on_clear_files,
        )
        self.btn_clear_files.pack(side="right")

        self.lbl_file_count = ctk.CTkLabel(
            self.file_card,
            text="No files selected",
            text_color="#94a3b8",
            font=ctk.CTkFont(size=12),
        )
        self.lbl_file_count.pack(anchor="w", padx=16, pady=(0, 10))

        # 3. Destination Directory Card
        self.out_card = ctk.CTkFrame(self.root, corner_radius=10)
        self.out_card.pack(fill="x", padx=24, pady=8)

        self.out_actions = ctk.CTkFrame(self.out_card, fg_color="transparent")
        self.out_actions.pack(fill="x", padx=14, pady=12)

        self.btn_select_output = ctk.CTkButton(
            self.out_actions,
            text="Output Folder",
            width=130,
            command=self._on_select_output,
        )
        self.btn_select_output.pack(side="left", padx=(0, 10))

        self.lbl_output_dir = ctk.CTkLabel(
            self.out_actions,
            text="Same folder as original files",
            text_color="#94a3b8",
            font=ctk.CTkFont(size=12),
        )
        self.lbl_output_dir.pack(side="left", fill="x", expand=True)

        # 4. Conversion Settings Card
        self.settings_card = ctk.CTkFrame(self.root, corner_radius=10)
        self.settings_card.pack(fill="x", padx=24, pady=8)

        # Format selector row
        self.fmt_row = ctk.CTkFrame(self.settings_card, fg_color="transparent")
        self.fmt_row.pack(fill="x", padx=14, pady=(12, 6))

        self.lbl_fmt = ctk.CTkLabel(self.fmt_row, text="Target Format:")
        self.lbl_fmt.pack(side="left", padx=(0, 10))

        self.combo_format = ctk.CTkComboBox(
            self.fmt_row,
            values=["JPEG (.jpg)", "PNG (.png)", "WEBP (.webp)"],
            width=140,
            command=self._on_format_changed,
        )
        self.combo_format.set("JPEG (.jpg)")
        self.combo_format.pack(side="left")

        # Quality slider row
        self.quality_row = ctk.CTkFrame(self.settings_card, fg_color="transparent")
        self.quality_row.pack(fill="x", padx=14, pady=6)

        self.lbl_quality = ctk.CTkLabel(self.quality_row, text="Quality: 92%")
        self.lbl_quality.pack(side="left", padx=(0, 10))

        self.slider_quality = ctk.CTkSlider(
            self.quality_row,
            from_=50,
            to=100,
            number_of_steps=50,
            command=self._on_quality_changed,
        )
        self.slider_quality.set(92)
        self.slider_quality.pack(side="left", fill="x", expand=True, padx=10)

        # Checkboxes row
        self.chk_row = ctk.CTkFrame(self.settings_card, fg_color="transparent")
        self.chk_row.pack(fill="x", padx=14, pady=(6, 12))

        self.chk_exif = ctk.CTkCheckBox(self.chk_row, text="Preserve EXIF metadata (GPS, date, camera)")
        self.chk_exif.select()
        self.chk_exif.pack(side="left", padx=(0, 15))

        self.chk_overwrite = ctk.CTkCheckBox(self.chk_row, text="Overwrite existing")
        self.chk_overwrite.pack(side="left")

        # 5. Progress & Action Section
        self.progress_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=24, pady=10)

        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, height=12)
        self.progress_bar.set(0.0)
        self.progress_bar.pack(fill="x", pady=(0, 6))

        self.lbl_status = ctk.CTkLabel(
            self.progress_frame,
            text="Ready to convert",
            text_color="#94a3b8",
            font=ctk.CTkFont(size=12),
        )
        self.lbl_status.pack(anchor="w")

        # Buttons (Start & Cancel)
        self.action_row = ctk.CTkFrame(self.root, fg_color="transparent")
        self.action_row.pack(fill="x", padx=24, pady=(6, 18))

        self.btn_convert = ctk.CTkButton(
            self.action_row,
            text="Convert All",
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#16a34a",
            hover_color="#15803d",
            height=44,
            command=self._start_conversion,
        )
        self.btn_convert.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.btn_cancel = ctk.CTkButton(
            self.action_row,
            text="Cancel",
            font=ctk.CTkFont(size=15),
            fg_color="#475569",
            hover_color="#334155",
            height=44,
            width=100,
            state="disabled",
            command=self._cancel_conversion,
        )
        self.btn_cancel.pack(side="right")

    def _on_format_changed(self, choice: str):
        if "PNG" in choice:
            self.slider_quality.configure(state="disabled")
            self.lbl_quality.configure(text="Quality: Lossless (PNG)")
        else:
            self.slider_quality.configure(state="normal")
            self.lbl_quality.configure(text=f"Quality: {int(self.slider_quality.get())}%")

    def _on_quality_changed(self, val: float):
        self.lbl_quality.configure(text=f"Quality: {int(val)}%")

    def _on_select_files(self):
        paths = filedialog.askopenfilenames(
            title="Select HEIC/HEIF files",
            filetypes=[("HEIC Files", "*.heic *.HEIC *.heif *.HEIF"), ("All Files", "*.*")],
        )
        if paths:
            for p in paths:
                path_obj = Path(p)
                if path_obj not in self.selected_files:
                    self.selected_files.append(path_obj)
            self._update_file_count_label()

    def _on_select_folder(self):
        folder = filedialog.askdirectory(title="Select folder with HEIC images")
        if folder:
            p = Path(folder)
            found = [f for f in p.glob("*") if f.is_file() and f.suffix.lower() in (".heic", ".heif")]
            for f in found:
                if f not in self.selected_files:
                    self.selected_files.append(f)
            self._update_file_count_label()

    def _on_clear_files(self):
        self.selected_files.clear()
        self._update_file_count_label()
        self.progress_bar.set(0.0)
        self.lbl_status.configure(text="Queue cleared")

    def _on_select_output(self):
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            self.output_dir = Path(folder)
            self.lbl_output_dir.configure(text=str(self.output_dir))

    def _update_file_count_label(self):
        count = len(self.selected_files)
        if count == 0:
            self.lbl_file_count.configure(text="No files selected")
        elif count == 1:
            self.lbl_file_count.configure(text=f"1 file queued: {self.selected_files[0].name}")
        else:
            self.lbl_file_count.configure(text=f"{count} files queued")

    def _start_conversion(self):
        if not self.selected_files:
            messagebox.showwarning("No Files", "Please select one or more HEIC files first.")
            return

        choice = self.combo_format.get()
        if "PNG" in choice:
            fmt = OutputFormat.PNG
        elif "WEBP" in choice:
            fmt = OutputFormat.WEBP
        else:
            fmt = OutputFormat.JPEG

        options = ConversionOptions(
            format=fmt,
            quality=int(self.slider_quality.get()),
            keep_exif=bool(self.chk_exif.get()),
            auto_orient=True,
            output_dir=self.output_dir,
            overwrite=bool(self.chk_overwrite.get()),
        )

        self.is_converting = True
        self.btn_convert.configure(state="disabled")
        self.btn_select_files.configure(state="disabled")
        self.btn_select_folder.configure(state="disabled")
        self.btn_clear_files.configure(state="disabled")
        self.btn_cancel.configure(state="normal")
        self.progress_bar.set(0.0)

        # Run background thread for responsiveness
        threading.Thread(
            target=self._run_conversion_worker,
            args=(list(self.selected_files), options),
            daemon=True,
        ).start()

    def _cancel_conversion(self):
        if self.is_converting:
            self.batch_runner.cancel()
            self.lbl_status.configure(text="Cancelling conversion...")
            self.btn_cancel.configure(state="disabled")

    def _run_conversion_worker(self, files: List[Path], options: ConversionOptions):
        def progress_callback(done: int, total: int, res: ConversionResult):
            def update():
                self.progress_bar.set(done / total)
                status_icon = "✓" if res.success else "✗"
                self.lbl_status.configure(
                    text=f"[{done}/{total}] {status_icon} {res.input_path.name}"
                )
            self.root.after(0, update)

        summary = self.batch_runner.convert_batch(
            files, options=options, on_progress=progress_callback
        )

        def complete():
            self.is_converting = False
            self.btn_convert.configure(state="normal")
            self.btn_select_files.configure(state="normal")
            self.btn_select_folder.configure(state="normal")
            self.btn_clear_files.configure(state="normal")
            self.btn_cancel.configure(state="disabled")

            if summary.cancelled:
                self.lbl_status.configure(text=f"Cancelled. Converted {summary.successful}/{summary.total_files} files.")
                messagebox.showwarning("Cancelled", f"Conversion cancelled. Processed {summary.successful} files.")
            else:
                self.lbl_status.configure(
                    text=f"Done! {summary.successful} succeeded, {summary.failed} failed in {summary.total_duration_seconds:.1f}s"
                )
                messagebox.showinfo(
                    "Conversion Finished",
                    f"Successfully converted {summary.successful} of {summary.total_files} files in {summary.total_duration_seconds:.2f}s.",
                )

        self.root.after(0, complete)

    def run(self):
        """Starts the Tkinter event loop."""
        self.root.mainloop()


def main():
    try:
        app = HeicConverterApp()
        app.run()
    except RuntimeError as e:
        print(f"Error launching GUI: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
