@echo off
rem Lays out your game files for bo2-360-nx without building anything. It needs Python 3.8 or later (python.org).
setlocal
cd /d "%~dp0"
set "PY="
python -c "import sys; sys.exit(sys.version_info < (3, 8))" >nul 2>nul && set "PY=python"
if not defined PY py -3 -c "import sys; sys.exit(sys.version_info < (3, 8))" >nul 2>nul && set "PY=py -3"
if not defined PY (
  echo.
  echo Python was not found. This tool needs it:
  echo   1. Download Python from https://www.python.org/downloads/
  echo   2. While installing, tick "Add python.exe to PATH".
  echo   3. Double-click this file again.
  echo.
  pause
  exit /b 1
)
%PY% extract.py %*
echo.
pause
