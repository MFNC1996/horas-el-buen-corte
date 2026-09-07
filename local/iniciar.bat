@echo off
REM Doble clic para encender el servidor a mano (Windows).
setlocal
cd /d "%~dp0."
set "PY="
py -3 -c "import sys" >nul 2>&1
if not errorlevel 1 set "PY=py -3"
if defined PY goto :ok
python -c "import sys" >nul 2>&1
if not errorlevel 1 set "PY=python"
:ok
if not defined PY (
  echo ERROR: no encontre Python 3. Bajalo de python.org y marca
  echo "Add Python to PATH" al instalarlo.
  pause
  exit /b 1
)
%PY% servidor.py
pause
