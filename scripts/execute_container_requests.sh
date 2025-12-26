#!/bin/bash
# Script para executar post_boot e register_microservice em container privado
# Executado na VM via SSH

# Não usar set -e para permitir tratamento de erros
set +e

CONTAINER_URL="${1:-}"
AUTH_TOKEN="${2:-}"

if [ -z "$CONTAINER_URL" ] || [ -z "$AUTH_TOKEN" ]; then
  echo "❌ Erro: CONTAINER_URL e AUTH_TOKEN são obrigatórios"
  echo "Uso: $0 <container_url> <auth_token>"
  exit 1
fi

echo "=========================================="
echo "Executando requisições no container privado"
echo "=========================================="
echo "Container URL: $CONTAINER_URL"
echo ""

# Função para fazer requisição HTTP com retry
make_request() {
  local endpoint=$1
  local method=${2:-GET}
  local max_retries=${3:-5}
  local retry_delay=${4:-10}
  
  local url="${CONTAINER_URL}${endpoint}"
  local http_code="000"
  local response_body=""
  
  for i in $(seq 1 $max_retries); do
    echo "Tentativa $i/$max_retries: $method $endpoint"
    
    if [ "$method" == "POST" ]; then
      result=$(curl -k -L -s -w "\n%{http_code}" -X POST "$url" \
        -H "Authorization: TOKEN $AUTH_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{}' \
        --max-time 60 --connect-timeout 30 2>/dev/null || echo -e "\n000")
    else
      result=$(curl -k -L -s -w "\n%{http_code}" "$url" \
        --max-time 30 --connect-timeout 10 2>/dev/null || echo -e "\n000")
    fi
    
    response_body=$(echo "$result" | head -n -1)
    http_code=$(echo "$result" | tail -n 1)
    
    echo "  HTTP Code: $http_code"
    
    if [ "$http_code" == "200" ] || [ "$http_code" == "201" ]; then
      echo "  ✅ Sucesso!"
      echo "$response_body"
      return 0
    else
      echo "  ⚠️  Falhou (HTTP $http_code), aguardando ${retry_delay}s..."
      if [ $i -lt $max_retries ]; then
        sleep $retry_delay
      fi
    fi
  done
  
  echo "  ❌ Falhou após $max_retries tentativas"
  echo "$response_body"
  return 1
}

# 1. Verificar health_check primeiro
echo ""
echo "1️⃣ Verificando health_check..."
HEALTH_RESPONSE=$(make_request "/lib/health_check" "GET" 10 5)
HEALTH_CODE=$?

# Inicializar arquivo de resultados
echo "" > /tmp/container_results.txt

if [ $HEALTH_CODE -eq 0 ]; then
  POSTGRES_OK=$(echo "$HEALTH_RESPONSE" | grep -o '"postgres":[^,}]*' | grep -o 'true' || echo "")
  REDIS_OK=$(echo "$HEALTH_RESPONSE" | grep -o '"redis":[^,}]*' | grep -o 'true' || echo "")
  
  if [ -n "$POSTGRES_OK" ] && [ -n "$REDIS_OK" ]; then
    echo "✅ Health check OK (PostgreSQL e Redis conectados)"
    echo "HEALTH_STATUS=success" >> /tmp/container_results.txt
  else
    echo "⚠️  Health check parcial (PostgreSQL: ${POSTGRES_OK:-false}, Redis: ${REDIS_OK:-false})"
    echo "HEALTH_STATUS=partial" >> /tmp/container_results.txt
  fi
else
  echo "⚠️  Health check falhou, mas continuando..."
  echo "HEALTH_STATUS=failed" >> /tmp/container_results.txt
  echo "HEALTH_RESPONSE<<EOF" >> /tmp/container_results.txt
  echo "$HEALTH_RESPONSE" >> /tmp/container_results.txt
  echo "EOF" >> /tmp/container_results.txt
fi

# 2. Executar post_boot
echo ""
echo "2️⃣ Executando post_boot..."
POST_BOOT_RESPONSE=$(make_request "/lib/post_boot" "POST" 5 10)
POST_BOOT_CODE=$?

if [ $POST_BOOT_CODE -eq 0 ]; then
  echo "POST_BOOT_STATUS=success" >> /tmp/container_results.txt
  echo "POST_BOOT_HTTP_CODE=200" >> /tmp/container_results.txt
  echo "POST_BOOT_RESPONSE<<EOF" >> /tmp/container_results.txt
  echo "$POST_BOOT_RESPONSE" >> /tmp/container_results.txt
  echo "EOF" >> /tmp/container_results.txt
else
  echo "POST_BOOT_STATUS=failed" >> /tmp/container_results.txt
  echo "POST_BOOT_HTTP_CODE=000" >> /tmp/container_results.txt
  echo "POST_BOOT_RESPONSE<<EOF" >> /tmp/container_results.txt
  echo "$POST_BOOT_RESPONSE" >> /tmp/container_results.txt
  echo "EOF" >> /tmp/container_results.txt
fi

# 3. Executar register_microservice
echo ""
echo "3️⃣ Executando register_microservice..."
REGISTER_RESPONSE=$(make_request "/lib/register_microservice" "POST" 3 5)
REGISTER_CODE=$?

if [ $REGISTER_CODE -eq 0 ]; then
  echo "REGISTER_STATUS=success" >> /tmp/container_results.txt
  echo "REGISTER_HTTP_CODE=200" >> /tmp/container_results.txt
  echo "REGISTER_RESPONSE<<EOF" >> /tmp/container_results.txt
  echo "$REGISTER_RESPONSE" >> /tmp/container_results.txt
  echo "EOF" >> /tmp/container_results.txt
else
  echo "REGISTER_STATUS=failed" >> /tmp/container_results.txt
  echo "REGISTER_HTTP_CODE=000" >> /tmp/container_results.txt
  echo "REGISTER_RESPONSE<<EOF" >> /tmp/container_results.txt
  echo "$REGISTER_RESPONSE" >> /tmp/container_results.txt
  echo "EOF" >> /tmp/container_results.txt
fi

# Exibir resumo
echo ""
echo "=========================================="
echo "Resumo dos resultados"
echo "=========================================="
cat /tmp/container_results.txt
echo ""

# Verificar se pelo menos uma operação foi bem-sucedida
if grep -q "POST_BOOT_STATUS=success\|REGISTER_STATUS=success" /tmp/container_results.txt; then
  echo "✅ Script concluído com sucesso parcial. Resultados salvos em /tmp/container_results.txt"
  exit 0
else
  echo "⚠️  Script concluído, mas nenhuma operação foi bem-sucedida. Resultados salvos em /tmp/container_results.txt"
  exit 1
fi

