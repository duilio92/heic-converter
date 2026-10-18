"""GUI package entry point."""

def run_gui():
    """Launches the graphical user interface."""
    from heic_converter.gui.app import main
    main()

__all__ = ["run_gui"]
