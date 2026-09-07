@echo off
REM ---------------------------------------------------------------------
REM  Deja el control de horas encendido siempre en este PC con Windows:
REM  arranca solo al encender y se levanta solo si se cae.
REM  No necesita permisos de administrador.
REM ---------------------------------------------------------------------
setlocal
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
  echo ERROR: no encontre Python.
  echo Instalalo desde https://www.python.org/downloads/
  echo IMPORTANTE: marca la casilla "Add Python to PATH" al instalar.
  pause
  exit /b 1
)

if not exist "registro" mkdir "registro"

REM Envoltorio que reinicia el servidor si se cae
> "%~dp0vigilante.bat" (
  echo @echo off
  echo cd /d "%~dp0"
  echo :bucle
  echo python servidor.py ^>^> "registro\salida.log" 2^>^&1
  echo timeout /t 5 /nobreak ^>nul
  echo goto bucle
)

REM Lanzador sin ventana
> "%~dp0oculto.vbs" (
  echo Set s = CreateObject^("WScript.Shell"^)
  echo s.Run """%~dp0vigilante.bat""", 0, False
)

set "INICIO=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
> "%INICIO%\ControlDeHoras.vbs" (
  echo Set s = CreateObject^("WScript.Shell"^)
  echo s.Run """%~dp0vigilante.bat""", 0, False
)

start "" wscript.exe "%~dp0oculto.vbs"

echo.
echo ==========================================================
echo   Listo. El control de horas queda encendido siempre.
echo ==========================================================
echo.
echo   - Arranca solo cada vez que enciendas el PC.
echo   - Si se cae, se levanta solo a los 5 segundos.
echo.
echo   IMPORTANTE, dos cosas a mano:
echo.
echo   1. Que Windows inicie sesion solo: escribe netplwiz en el
echo      buscador y desmarca "Los usuarios deben escribir su nombre".
echo.
echo   2. Que el PC no se suspenda: Configuracion ^> Sistema ^>
echo      Inicio/apagado ^> Suspension: Nunca.
echo.
echo   Para saber en que direccion quedo, abre registro\salida.log
echo   o entra a http://localhost:8080 en este mismo PC.
echo.
echo   Para apagarlo: borra ControlDeHoras.vbs de la carpeta
echo   de Inicio (pega esto en el explorador:  shell:startup ^)
echo.
pause
