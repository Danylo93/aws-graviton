#!/bin/bash
# Script para provisionar VM Runner antes do workflow
# Usado no GitHub Actions para iniciar a VM antes de usar o runner

set -e

RG_NAME="${RG_NAME:-RG-ARCS-PORSCHECUP-HML2}"
VM_NAME="${VM_NAME:-vm-runner-github-hml2}"

echo "=========================================="
echo "Provisionando VM Runner"
echo "=========================================="
echo "Resource Group: $RG_NAME"
echo "VM Name: $VM_NAME"
echo ""

# Verificar se VM existe
VM_EXISTS=$(az vm show \
  --resource-group "$RG_NAME" \
  --name "$VM_NAME" \
  --query "id" \
  -o tsv 2>/dev/null || echo "")

if [ -z "$VM_EXISTS" ]; then
  echo "❌ VM não encontrada: $VM_NAME"
  echo "   Execute 'terraform apply' primeiro para criar a VM"
  exit 1
fi

# Verificar status atual
VM_STATUS=$(az vm show \
  --resource-group "$RG_NAME" \
  --name "$VM_NAME" \
  --show-details \
  --query "powerState" \
  -o tsv 2>/dev/null || echo "Unknown")

echo "Status atual da VM: $VM_STATUS"

# Iniciar VM se estiver desligada
if [ "$VM_STATUS" != "VM running" ]; then
  echo ""
  echo "Iniciando VM..."
  az vm start \
    --resource-group "$RG_NAME" \
    --name "$VM_NAME" \
    --no-wait

  echo "Aguardando VM iniciar..."
  az vm wait \
    --resource-group "$RG_NAME" \
    --name "$VM_NAME" \
    --created \
    --timeout 300

  echo "✅ VM iniciada com sucesso!"
else
  echo "✅ VM já está rodando"
fi

# Aguardar um pouco para garantir que o runner está pronto
echo ""
echo "Aguardando runner ficar pronto..."
sleep 30

# Verificar status final
VM_STATUS_FINAL=$(az vm show \
  --resource-group "$RG_NAME" \
  --name "$VM_NAME" \
  --show-details \
  --query "powerState" \
  -o tsv 2>/dev/null || echo "Unknown")

echo ""
echo "=========================================="
echo "✅ VM Runner provisionada!"
echo "=========================================="
echo "VM Name: $VM_NAME"
echo "VM Status: $VM_STATUS_FINAL"
echo ""


