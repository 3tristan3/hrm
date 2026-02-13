#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${ENV_FILE:-.env.docker}"
REMOTE="${REMOTE:-origin}"
BRANCH="${BRANCH:-main}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing env file: $ENV_FILE"
  echo "Create it first, for example: cp .env.docker.example .env.docker"
  exit 1
fi

echo "[1/5] Fetching latest code from $REMOTE/$BRANCH ..."
git fetch "$REMOTE"

echo "[2/5] Resetting working tree to $REMOTE/$BRANCH ..."
git reset --hard "$REMOTE/$BRANCH"
git clean -fd -e .env.docker

echo "[3/5] Building containers ..."
docker compose --env-file "$ENV_FILE" build

echo "[4/5] Starting services ..."
docker compose --env-file "$ENV_FILE" up -d

echo "[5/5] Service status:"
docker compose --env-file "$ENV_FILE" ps

echo "Deploy finished."
