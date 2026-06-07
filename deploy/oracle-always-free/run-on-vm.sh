#!/usr/bin/env bash
set -euo pipefail

if ! command -v docker >/dev/null 2>&1; then
  echo "docker no esta instalado" >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "docker compose plugin no esta disponible" >&2
  exit 1
fi

if [[ ! -f .env ]]; then
  echo "falta .env en raiz del repo" >&2
  exit 1
fi

mkdir -p .state
docker compose up -d --build
docker compose ps
