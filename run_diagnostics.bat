@echo off
echo Running Huntarr diagnostics...
echo This will check for common Windows-specific issues.

if exist "Huntarr.exe" (
    Huntarr.exe -m src.primary.diagnose_windows
) else (
    python -m src.primary.diagnose_windows
)

echo.
echo Diagnostics complete. Press any key to exit.
pause > nul 