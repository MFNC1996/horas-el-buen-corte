#!/bin/bash
# Apaga el arranque automatico. Los datos NO se borran.
ETIQUETA="cl.elbuencorte.horas"
PLIST="$HOME/Library/LaunchAgents/$ETIQUETA.plist"
launchctl unload "$PLIST" 2>/dev/null || true
rm -f "$PLIST"
echo
echo "  Arranque automatico desactivado."
echo "  Los datos siguen intactos en datos.sqlite3."
echo "  Para volver a encenderlo: doble clic en instalar-mac.command"
echo
read -r -p "Enter para cerrar..."
