@echo off
REM Apaga el arranque automatico. Los datos NO se borran.
setlocal
set "INICIO=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
if exist "%INICIO%\ControlDeHoras.vbs" del "%INICIO%\ControlDeHoras.vbs"
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im pythonw.exe >nul 2>&1
echo.
echo   Arranque automatico desactivado y servidor detenido.
echo   Los datos siguen intactos en datos.sqlite3.
echo   Para volver a encenderlo: doble clic en instalar-windows.bat
echo.
pause
