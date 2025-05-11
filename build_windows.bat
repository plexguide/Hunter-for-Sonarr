@echo off
echo Building Huntarr for Windows...

:: Create necessary directories
mkdir config\logs 2>nul
mkdir config\db 2>nul
mkdir config\settings 2>nul

:: Install required packages
pip install -r requirements.txt
pip install pyinstaller

:: Build with PyInstaller
pyinstaller huntarr.spec

echo.
echo Build completed. The executable can be found in the dist\Huntarr directory.
echo.
echo To install as a Windows service:
echo   1. Navigate to dist\Huntarr
echo   2. Run: HuntarrService.exe --install-service
echo.
echo To start the application:
echo   Run: dist\Huntarr\Huntarr.exe
echo.
pause
