@echo off
echo ================================================
echo Huntarr Windows Path Fix Updater
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

:: Stop Huntarr service if running
sc query Huntarr > nul 2>&1
if %errorlevel% equ 0 (
    echo Stopping Huntarr service...
    net stop Huntarr
    timeout /t 3 /nobreak > nul
) else (
    echo Huntarr service not found or not running.
)

:: Copy the updated files to the Program Files location
echo Applying path fix update...
set INSTALL_DIR=C:\Program Files\Huntarr
if not exist "%INSTALL_DIR%" (
    echo ERROR: Huntarr installation not found at %INSTALL_DIR%
    echo Please install Huntarr first.
    pause
    exit /B 1
)

:: Copy the fixed windows_path_fix.py file
copy /Y "src\primary\windows_path_fix.py" "%INSTALL_DIR%\src\primary\windows_path_fix.py"
if %errorlevel% neq 0 (
    echo ERROR: Failed to update windows_path_fix.py
    pause
    exit /B 1
)

echo Files updated successfully.
echo.

:: Start the service
echo Starting Huntarr service...
sc start Huntarr
timeout /t 5 /nobreak > nul

:: Check if service started
sc query Huntarr | find "RUNNING" > nul
if %errorlevel% equ 0 (
    echo Huntarr service started successfully.
) else (
    echo WARNING: Huntarr service could not be started automatically.
    echo You may need to start it manually or restart your computer.
)

echo.
echo ================================================
echo Update completed. Try accessing the web interface at:
echo http://localhost:9705
echo.
echo If you still experience issues, please use the diagnostic tool:
echo %INSTALL_DIR%\src\primary\diagnose_windows.py
echo ================================================
echo.

pause 