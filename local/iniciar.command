#!/bin/bash
# Doble clic para encender el servidor a mano (macOS).
cd "$(dirname "$0")" || exit 1
exec /usr/bin/caffeinate -s python3 servidor.py
