#!/usr/bin/env bash
set -euo pipefail

ROLE="${SERVICE_ROLE:-backend}"

if [[ "$ROLE" == "frontend" ]]; then
  echo "Starting frontend service (Bun)..."
  cd frontend
  bun install
  bun run build
  bun run start
else
  echo "Starting backend service..."
  cd backend
  pip install -r requirements.txt
  uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
fi
