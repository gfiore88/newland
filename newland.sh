#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

show_menu() {
  echo ""
  echo "=================================================="
  echo "          🌿 NEWLAND CONTROL PANEL 🌿            "
  echo "=================================================="
  echo "  1) 🧹 Reset Mondo (Pulisce DB e processi)"
  echo "  2) 🚀 Avvia Server Live (http://0.0.0.0:8765)"
  echo "  3) 👤 Fai Entrare un Abitante (Varca la Soglia)"
  echo "  4) 🚪 Esci"
  echo "=================================================="
}

if [ $# -gt 0 ]; then
  case "$1" in
    reset|1)
      ./scripts/reset-world.sh
      exit 0
      ;;
    start|live|2)
      ./scripts/start-live.sh
      exit 0
      ;;
    arrive|3)
      shift
      NAME="${1:-Elia Moretti}"
      ./scripts/arrive.sh "$NAME"
      exit 0
      ;;
    *)
      echo "Uso: ./newland.sh [reset|start|arrive <nome>]"
      exit 1
      ;;
  esac
fi

show_menu
read -rp "Seleziona un'opzione [1-4]: " choice

case "$choice" in
  1)
    ./scripts/reset-world.sh
    ;;
  2)
    ./scripts/start-live.sh
    ;;
  3)
    read -rp "Nome dell'abitante [default: Elia Moretti]: " name
    name="${name:-Elia Moretti}"
    ./scripts/arrive.sh "$name"
    ;;
  4)
    echo "Arrivederci!"
    exit 0
    ;;
  *)
    echo "Opzione non valida."
    exit 1
    ;;
esac
