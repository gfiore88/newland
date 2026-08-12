#!/usr/bin/env bash
set -euo pipefail

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8765}"
MODEL="${MODEL:-qwen2.5:3b}"
CHRONICLE_MODEL="${CHRONICLE_MODEL:-qwen3:8b}"
DB_PATH="${1:-data/newland.db}"

echo "🌿 Liberazione eventuale porta ${PORT}..."
lsof -ti:"${PORT}" | xargs kill -9 2>/dev/null || true

echo "🚀 Avvio Newland Live Supervisor su http://${HOST}:${PORT} (Agente: ${MODEL}, Cronista: ${CHRONICLE_MODEL})..."
exec uv run newland --db "$DB_PATH" live --host "$HOST" --port "$PORT" --model "$MODEL" --chronicle-model "$CHRONICLE_MODEL"
