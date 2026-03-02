#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${ENV_FILE:-.env.docker}"
EXAMPLE_ENV_FILE="${EXAMPLE_ENV_FILE:-.env.docker.example}"
REMOTE="${REMOTE:-origin}"
BRANCH="${BRANCH:-main}"
RESET_DB="${RESET_DB:-0}"          # 1 => reset mysql_data volume
SKIP_GIT_UPDATE="${SKIP_GIT_UPDATE:-0}"  # 1 => skip fetch/reset

info() { echo "[INFO] $*"; }
warn() { echo "[WARN] $*" >&2; }
fail() { echo "[ERROR] $*" >&2; exit 1; }

usage() {
  cat <<'EOF'
Usage:
  ./deploy.sh
  RESET_DB=1 ./deploy.sh
  SKIP_GIT_UPDATE=1 ./deploy.sh

Env vars:
  ENV_FILE=.env.docker
  EXAMPLE_ENV_FILE=.env.docker.example
  REMOTE=origin
  BRANCH=main
  RESET_DB=0|1
  SKIP_GIT_UPDATE=0|1
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --reset-db)
      RESET_DB=1
      shift
      ;;
    --skip-git)
      SKIP_GIT_UPDATE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "Unknown argument: $1"
      ;;
  esac
done

command -v git >/dev/null 2>&1 || fail "git is not installed."
command -v docker >/dev/null 2>&1 || fail "docker is not installed."
docker compose version >/dev/null 2>&1 || fail "docker compose plugin is not available."

if [[ ! -f "$ENV_FILE" ]]; then
  if [[ -f .env.docker.example ]]; then
    cp .env.docker.example "$ENV_FILE"
    warn "Created $ENV_FILE from .env.docker.example."
    warn "Please edit $ENV_FILE with your real passwords/domain, then rerun ./deploy.sh."
    exit 1
  fi
  fail "Missing env file: $ENV_FILE"
fi

# Fix accidental CRLF copied from Windows.
sed -i 's/\r$//' "$ENV_FILE"

sync_missing_env_keys_from_example() {
  local env_file="$1"
  local example_file="$2"
  local added_count=0
  local line=""
  local key=""

  [[ -f "$example_file" ]] || return 0
  sed -i 's/\r$//' "$example_file"

  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%$'\r'}"
    [[ -z "${line//[[:space:]]/}" ]] && continue
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)= ]]; then
      key="${BASH_REMATCH[1]}"
      if ! grep -Eq "^[[:space:]]*${key}=" "$env_file"; then
        printf '\n%s\n' "$line" >> "$env_file"
        added_count=$((added_count + 1))
      fi
    fi
  done < "$example_file"

  if (( added_count > 0 )); then
    info "已从 $example_file 补齐 $added_count 个新增配置到 $env_file（未覆盖已有值）。"
  fi
}

warn_empty_env_keys() {
  local env_file="$1"
  local line=""
  local key=""
  local value=""
  local -a empty_keys=()

  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%$'\r'}"
    [[ -z "${line//[[:space:]]/}" ]] && continue
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
      key="${BASH_REMATCH[1]}"
      value="${BASH_REMATCH[2]}"
      value="${value#"${value%%[![:space:]]*}"}"
      value="${value%"${value##*[![:space:]]}"}"
      if [[ -z "$value" ]]; then
        empty_keys+=("$key")
      fi
    fi
  done < "$env_file"

  if (( ${#empty_keys[@]} > 0 )); then
    warn "$env_file 中存在空值配置，请按需补全：${empty_keys[*]}"
  fi
}

compose() {
  docker compose --env-file "$ENV_FILE" "$@"
}

wait_healthy() {
  local service="$1"
  local timeout="${2:-180}"
  local elapsed=0
  local status=""
  local cid=""

  info "Waiting for service '$service' to become healthy (timeout ${timeout}s) ..."
  while (( elapsed < timeout )); do
    cid="$(compose ps -q "$service" 2>/dev/null || true)"
    if [[ -n "$cid" ]]; then
      status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$cid" 2>/dev/null || true)"
      if [[ "$status" == "healthy" || "$status" == "running" ]]; then
        info "Service '$service' is $status."
        return 0
      fi
      if [[ "$status" == "unhealthy" || "$status" == "exited" ]]; then
        warn "Service '$service' is $status."
        return 1
      fi
    fi
    sleep 3
    elapsed=$((elapsed + 3))
  done

  warn "Service '$service' did not become healthy in ${timeout}s."
  return 1
}

if [[ "$SKIP_GIT_UPDATE" != "1" ]]; then
  info "[1/7] Fetching latest code from $REMOTE/$BRANCH ..."
  git fetch "$REMOTE"

  info "[2/7] Resetting working tree to $REMOTE/$BRANCH ..."
  git reset --hard "$REMOTE/$BRANCH"
  git clean -fd -e "$ENV_FILE"
else
  info "[1/7] SKIP_GIT_UPDATE=1, skip fetch/reset."
fi

info "[3/7] Syncing env keys from example (append only) ..."
sync_missing_env_keys_from_example "$ENV_FILE" "$EXAMPLE_ENV_FILE"
warn_empty_env_keys "$ENV_FILE"

if [[ "$RESET_DB" == "1" ]]; then
  info "[4/7] RESET_DB=1, recreating containers and volumes ..."
  compose down --remove-orphans -v || true
else
  info "[4/7] Recreating containers (preserve database volume) ..."
  compose down --remove-orphans || true
fi

info "[5/7] Starting database ..."
compose up -d --build db
if ! wait_healthy db 180; then
  compose logs db --tail=200 || true
  fail "Database did not become healthy."
fi

info "[6/7] Starting backend ..."
compose up -d --build backend
if ! wait_healthy backend 240; then
  compose logs backend --tail=240 || true
  if compose logs backend --tail=240 2>/dev/null | grep -q "Access denied for user"; then
    warn "Detected MySQL credential mismatch."
    warn "Run again with database reset: RESET_DB=1 ./deploy.sh"
  fi
  fail "Backend did not become healthy."
fi

info "[7/7] Starting frontend services ..."
compose up -d --build web_apply web_admin
if ! wait_healthy web_apply 180; then
  warn "web_apply is not healthy yet, printing logs:"
  compose logs web_apply --tail=120 || true
fi
if ! wait_healthy web_admin 180; then
  warn "web_admin is not healthy yet, printing logs:"
  compose logs web_admin --tail=120 || true
fi

info "Service status:"
compose ps

info "Deploy finished."
