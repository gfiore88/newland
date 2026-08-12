#!/usr/bin/env bash
set -euo pipefail

NAME="${1:-Elia Moretti}"
LOCATION="${2:-cittadina_iniziale}"
DB_PATH="${3:-data/newland.db}"

echo "👤 Ingresso nuovo abitante: '${NAME}' in '${LOCATION}'..."
exec uv run newland --db "$DB_PATH" arrive --name "$NAME" --location "$LOCATION"
