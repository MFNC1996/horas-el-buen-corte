@echo off
REM ---------------------------------------------------------------------
REM  Deja el control de horas encendido siempre en este PC con Windows:
REM  arranca solo al encender y se levanta solo si se cae.
REM  No necesita permisos de administrador.
REM ---------------------------------------------------------------------
setlocal
cd /d "%~dp0."
title Instalar control de horas

REM --- Buscar Python de verdad -----------------------------------------
REM  Windows trae un "python.exe" falso que solo abre la Microsoft Store.
REM  Por eso no basta con "where python": hay que ejecutarlo y ver si anda.
set "PY="
py -3 -c "import sys" >nul 2>&1
if not errorlevel 1 set "PY=py -3"
if defined PY goto :haypython
python -c "import sys" >nul 2>&1
if not errorlevel 1 set "PY=python"
:haypython
if not defined PY goto :sinpython

echo   Python encontrado: %PY%
echo.

if not exist "registro" mkdir "registro"

REM --- Vigilante: relanza el servidor si se cae -------------------------
REM  ping en vez de timeout: timeout falla cuando el proceso corre oculto.
> "vigilante.bat" (
  echo @echo off
  echo cd /d "%%~dp0."
  echo :bucle
  echo %PY% servidor.py ^>^> "registro\salida.log" 2^>^&1
  echo ping -n 6 127.0.0.1 ^>nul
  echo goto bucle
)

REM --- Arranque automatico al iniciar sesion ----------------------------
set "INICIO=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
> "%INICIO%\ControlDeHoras.vbs" (
  echo Set s = CreateObject^("WScript.Shell"^)
  echo s.Run """%~dp0vigilante.bat""", 0, False
)

echo   Arranque automatico configurado.
echo.
echo ==========================================================
echo   IMPORTANTE: la primera vez, Windows va a preguntar si
echo   permite que Python acepte conexiones.
echo.
echo   Marca "Redes privadas" y dale PERMITIR ACCESO.
echo.
echo   Si le das cancelar, los celulares NO van a poder entrar
echo   y vas a tener que permitirlo despues a mano en el
echo   Firewall de Windows Defender.
echo ==========================================================
echo.
pause

REM  Esta primera vez lo abrimos VISIBLE, para que se vea el aviso del
REM  firewall y la direccion. De aqui en adelante arranca oculto solo.
start "Control de horas" cmd /k "%PY% servidor.py"

echo.
echo   Listo. En la ventana que se abrio esta la direccion.
echo   La que dice "Desde los celulares" es la que se manda por WhatsApp.
echo.
echo   Dos cosas que faltan, a mano y una sola vez:
echo.
echo   1. Que Windows inicie sesion solo: escribe  netplwiz  en el
echo      buscador y desmarca "Los usuarios deben escribir su nombre".
echo      Sin esto, despues de un corte de luz la app no vuelve sola.
echo.
echo   2. Que el PC no se suspenda: Configuracion ^> Sistema ^>
echo      Inicio/apagado ^> Suspension: Nunca.
echo.
echo   Para apagar el arranque automatico: doble clic en
echo   desinstalar-windows.bat
echo.
pause
exit /b 0

:sinpython
echo.
echo   ERROR: no encontre Python 3 en este equipo.
echo.
echo   Bajalo de https://www.python.org/downloads/
echo   Al instalarlo, MARCA LA CASILLA "Add Python to PATH"
echo   (esta abajo del todo en la primera pantalla y viene desmarcada).
echo.
echo   Despues vuelve a ejecutar este archivo.
echo.
pause
exit /b 1
