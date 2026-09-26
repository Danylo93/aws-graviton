#!/usr/bin/env bash
set -Eeuo pipefail
# Recebe um tar.gz via scp em /tmp/graviton-lab-<SHA>.tar.gz.
sha="${1:?commit obrigatório}"
[[ "$sha" =~ ^[0-9a-f]{40}$ ]] || { echo 'SHA inválido' >&2; exit 2; }
archive="/tmp/graviton-lab-${sha}.tar.gz"
trap 'rm -f "$archive"' EXIT
image="graviton-lab:${sha}"
docker load -i "$archive"
arch="$(docker image inspect "$image" --format '{{.Architecture}}')"
[[ "$arch" == 'arm64' ]] || { echo "Imagem incorreta: $arch" >&2; exit 3; }
previous="$(docker inspect graviton-lab --format '{{.Config.Image}}' 2>/dev/null || true)"
if [[ -n "$previous" ]]; then docker tag "$previous" graviton-lab:rollback; docker rm -f graviton-lab; fi
start() {
  docker run -d --name graviton-lab --restart unless-stopped \
    --memory 256m --cpus 1 --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m \
    -p 127.0.0.1:8080:8080 -e "APP_VERSION=$1" "$2" >/dev/null
}
start "$sha" "$image"
for attempt in 1 2 3 4 5 6 7 8 9 10; do
  if curl -fsS --max-time 2 http://127.0.0.1:8080/health >/dev/null; then
    echo "Deploy concluído: $sha ($arch)"; exit 0
  fi
  sleep 2
done
echo 'Health check falhou; restaurando versão anterior' >&2
docker logs --tail 30 graviton-lab >&2 || true
docker rm -f graviton-lab >/dev/null
if docker image inspect graviton-lab:rollback >/dev/null 2>&1; then
  start rollback graviton-lab:rollback
else
  echo 'Nenhuma versão anterior disponível' >&2
fi
exit 1
