@echo off
REM Build script for Windows 10
echo ====================================================
echo  Building HEIC Converter for Windows 10
echo ====================================================

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python is not found in PATH! Please install Python 3.8+ and add it to PATH.
    pause
    exit /b 1
)

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python scripts/build.py

echo.
echo Executable is located in the 'dist' folder.
pause
