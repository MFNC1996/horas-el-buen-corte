#!/bin/bash
# ---------------------------------------------------------------------------
# Deja el control de horas encendido siempre en este Mac:
#   - arranca solo al iniciar sesion
#   - si el servidor se cae, se levanta solo
#   - impide que el equipo se suspenda mientras corre
# No pide contrasena ni toca nada del sistema.
# ---------------------------------------------------------------------------
set -e
cd "$(dirname "$0")"
CARPETA="$(pwd)"
ETIQUETA="cl.elbuencorte.horas"
PLIST="$HOME/Library/LaunchAgents/$ETIQUETA.plist"

PY="$(command -v python3 || true)"
if [ -z "$PY" ]; then
  echo "ERROR: no encontre Python 3."
  echo "Instalalo desde https://www.python.org/downloads/ y vuelve a ejecutar esto."
  read -r -p "Enter para cerrar..."
  exit 1
fi

mkdir -p "$HOME/Library/LaunchAgents" "$CARPETA/registro"

cat > "$PLIST" <<PLISTEOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$ETIQUETA</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/caffeinate</string>
    <string>-s</string>
    <string>$PY</string>
    <string>$CARPETA/servidor.py</string>
  </array>
  <key>WorkingDirectory</key><string>$CARPETA</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$CARPETA/registro/salida.log</string>
  <key>StandardErrorPath</key><string>$CARPETA/registro/errores.log</string>
</dict>
</plist>
PLISTEOF

launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"
sleep 2

echo
echo "=========================================================="
echo "  Listo. El control de horas queda encendido siempre."
echo "=========================================================="
echo
echo "  - Arranca solo cada vez que enciendas el Mac."
echo "  - Si se cae, se levanta solo."
echo "  - El Mac no se va a suspender mientras corre."
echo
sleep 1
tail -n 20 "$CARPETA/registro/salida.log" 2>/dev/null || true
echo
echo "  IMPORTANTE, dos cosas que tienes que hacer a mano:"
echo
echo "  1. Que el Mac inicie sesion solo al encenderse:"
echo "     Configuracion del sistema > Usuarios y grupos >"
echo "     Inicio de sesion automatico > elige tu usuario."
echo
echo "  2. Que la pantalla se apague pero el equipo no duerma:"
echo "     Configuracion del sistema > Bloqueo de pantalla y Energia."
echo
echo "  Para apagarlo: doble clic en desinstalar-mac.command"
echo
read -r -p "Enter para cerrar..."
