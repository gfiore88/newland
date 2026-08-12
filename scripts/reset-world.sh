#!/usr/bin/env bash
set -euo pipefail

DB_PATH="${1:-data/newland.db}"
CHRONICLE_PATH="${2:-data/newland.chronicle.db}"

echo "🌿 Arresto eventuali processi Newland attivi..."
lsof -ti:8765 | xargs kill -9 2>/dev/null || true
pkill -9 -f "uv run newland" 2>/dev/null || true
pkill -9 -f "newland_engine" 2>/dev/null || true

echo "🧹 Eliminazione vecchi database ($DB_PATH, $CHRONICLE_PATH)..."
rm -f "$DB_PATH" "$CHRONICLE_PATH"

echo "✨ Reset completato! Il mondo Newland è ora vergine e pulito (0 abitanti)."
