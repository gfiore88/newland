#!/usr/bin/env bash
set -euo pipefail

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8765}"
MODEL="${MODEL:-dashscope:qwen-flash-character}"
FALLBACK_MODEL="${FALLBACK_MODEL:-ollama:qwen2.5:3b}"
CHRONICLE_MODEL="${CHRONICLE_MODEL:-qwen3:8b}"
CLOUD_TOKEN_CAP="${CLOUD_TOKEN_CAP:-100000}"
DB_PATH="${1:-data/newland.db}"

echo "🌿 Liberazione eventuale porta ${PORT}..."
lsof -ti:"${PORT}" | xargs kill -9 2>/dev/null || true

args=(
  --db "$DB_PATH" live
  --host "$HOST"
  --port "$PORT"
  --model "$MODEL"
  --chronicle-model "$CHRONICLE_MODEL"
)

if [[ -n "$FALLBACK_MODEL" ]]; then
  args+=(--model "$FALLBACK_MODEL")
fi

if [[ "$MODEL" == dashscope:* ]]; then
  args+=(--allow-cloud-live --cloud-token-cap "$CLOUD_TOKEN_CAP")
fi

echo "🚀 Avvio Newland Live su http://${HOST}:${PORT} (Agenti: ${MODEL}, fallback: ${FALLBACK_MODEL:-nessuno}, Cronista locale: ${CHRONICLE_MODEL})..."
exec uv run newland "${args[@]}"
