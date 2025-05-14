@echo off
echo ================================================
echo Huntarr Windows Installation Troubleshooter
echo ================================================
echo.

:: Check if running as administrator
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if %errorlevel% neq 0 (
    echo ERROR: Administrator privileges are required.
    echo Please right-click this batch file and select "Run as administrator".
    echo.
    pause
    exit /B 1
)

echo Running as administrator: OK
echo.

:: Check if the Huntarr service is running
echo Checking Huntarr service status...
sc query Huntarr > nul
if %errorlevel% equ 0 (
    echo Huntarr service found. Stopping service for maintenance...
    net stop Huntarr
    echo.
) else (
    echo Huntarr service not found or not accessible.
    echo.
)

:: Check if Python is installed
python --version > nul 2>&1
if %errorlevel% equ 0 (
    echo Python is installed.
) else (
    echo WARNING: Python is not installed or not in PATH.
    echo Only pre-built installer diagnostics will be available.
    echo.
)

:: Check for main executable
if exist "Huntarr.exe" (
    echo Huntarr executable found.
) else (
    echo WARNING: Huntarr.exe not found in the current directory.
    echo This script should be run from the Huntarr installation directory.
    echo.
)

:: Ensure config directory exists with proper permissions
echo Creating/checking config directory...
if not exist "config" (
    mkdir config
)
if not exist "config\logs" (
    mkdir config\logs
)

echo Setting permissions on config directory...
icacls "config" /grant Everyone:(OI)(CI)F
echo.

:: Check if a diagnostic file exists
if exist "src\primary\diagnose_windows.py" (
    echo Running diagnostic tool...
    echo.
    if exist "Huntarr.exe" (
        Huntarr.exe -m src.primary.diagnose_windows
    ) else (
        python -m src.primary.diagnose_windows
    )
) else (
    echo Diagnostic tool not found.
    echo.
)

:: Check for Flask dependencies
echo.
echo Installing missing dependencies...
if exist "requirements.txt" (
    pip install -r requirements.txt
    echo Dependencies installed/updated.
) else (
    echo WARNING: requirements.txt not found.
    echo Installing core dependencies manually...
    pip install Flask==3.0.0 Werkzeug==3.0.1 Jinja2==3.1.2 MarkupSafe==2.1.3 itsdangerous==2.1.2 waitress==2.1.2 pywin32==306 bcrypt==4.1.2 qrcode[pil]==7.4.2 pyotp==2.9.0
)
echo.

:: Uninstall and reinstall the service
echo Attempting to repair Windows service...
if exist "Huntarr.exe" (
    echo Removing existing service...
    Huntarr.exe --remove-service
    timeout /t 2 /nobreak > nul
    echo Installing service...
    Huntarr.exe --install-service
    echo.
    echo Starting service...
    net start Huntarr
) else (
    echo Cannot repair service: Huntarr.exe not found.
)

echo.
echo ================================================
echo Troubleshooting complete
echo ================================================
echo.
echo If you're still experiencing issues, please check:
echo 1. Windows Event Viewer for application errors
echo 2. Logs in the config\logs directory
echo 3. Make sure port 9705 is not blocked by firewall
echo.
echo You can also try running Huntarr directly (not as a service):
echo   Huntarr.exe
echo.
echo Visit https://github.com/plexguide/Huntarr.io for more help
echo.
pause 