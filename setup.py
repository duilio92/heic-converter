from setuptools import setup, find_packages

setup(
    name="heic-converter",
    version="1.0.0",
    description="Cross-platform HEIC to JPEG/PNG/WEBP converter with CLI and GUI",
    author="HEIC Converter Project",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "Pillow>=10.0.0",
        "pillow-heif>=0.16.0",
        "customtkinter>=5.2.0",
        "darkdetect>=0.8.0",
    ],
    entry_points={
        "console_scripts": [
            "heic-converter=heic_converter.cli.main:cli_main",
            "heic-converter-gui=heic_converter.gui.app:main",
        ],
    },
    python_requires=">=3.8",
)
