@echo off
setlocal
title Excel Consolidator
cd /d "%~dp0"
echo Starting Excel Consolidator...
echo.
for %%P in ("%~dp0.launcher-venv\Scripts\python.exe" "%~dp0.venv\Scripts\python.exe" "%~dp0.review-env\Scripts\python.exe") do (
    "%%~P" -c "import sys; sys.exit(sys.version_info < (3, 12))" >nul 2>&1
    if not errorlevel 1 (
        "%%~P" "%~dp0launcher.py" %*
        goto finished
    )
)
py -3 -c "import sys; sys.exit(sys.version_info < (3, 12))" >nul 2>&1
if not errorlevel 1 (
    py -3 "%~dp0launcher.py" %*
    goto finished
)
python -c "import sys; sys.exit(sys.version_info < (3, 12))" >nul 2>&1
if not errorlevel 1 (
    python "%~dp0launcher.py" %*
    goto finished
)
echo Python 3.12 or newer is needed for first-time setup.
echo Install Python from https://www.python.org/downloads/windows/
echo Enable "Add python.exe to PATH" in the installer, then double-click this file again.
pause
exit /b 1
:finished
if errorlevel 1 (
    echo.
    echo Excel Consolidator could not start. Please read the message above.
    pause
    exit /b 1
)
endlocal
