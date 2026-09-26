#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
command -v go >/dev/null || { echo 'Instale Go >= 1.22' >&2; exit 1; }
go test ./...
mkdir -p bin
CGO_ENABLED=0 GOOS=linux GOARCH=arm64 go build -o bin/server ./app
file bin/server || true
if command -v docker >/dev/null; then
  docker build --platform linux/arm64 -t graviton-lab:local .
  docker image inspect graviton-lab:local --format 'Imagem: {{.Os}}/{{.Architecture}}'
fi
printf '\nCompilado para ARM64. Na instância Graviton, rode: uname -m (aarch64).\n'
