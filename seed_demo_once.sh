#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR/backend_django"

if [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
elif [[ -x ".venv/Scripts/python.exe" ]]; then
  PYTHON_BIN=".venv/Scripts/python.exe"
else
  PYTHON_BIN="python"
fi

echo "[seed] using python: $PYTHON_BIN"
echo "[seed] running migrations..."
"$PYTHON_BIN" manage.py migrate --noinput

echo "[seed] ensuring default regions..."
"$PYTHON_BIN" manage.py ensure_default_regions

echo "[seed] creating demo data once (5 jobs + 20 applications)..."
"$PYTHON_BIN" manage.py seed_vps_demo_once --job-count 5 --count 20

echo "[seed] done."
