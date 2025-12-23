#!/bin/bash
# Script para desligar/destruir VM Runner após o workflow
# Usado no GitHub Actions para economizar custos

set -e

RG_NAME="${RG_NAME:-RG-ARCS-PORSCHECUP-HML2}"
VM_NAME="${VM_NAME:-vm-runner-github-hml2}"
DESTROY_MODE="${DESTROY_MODE:-deallocate}" # deallocate (desligar) ou delete (destruir)

echo "=========================================="
echo "Finalizando VM Runner"
echo "=========================================="
echo "Resource Group: $RG_NAME"
echo "VM Name: $VM_NAME"
echo "Mode: $DESTROY_MODE"
echo ""

# Verificar se VM existe
VM_EXISTS=$(az vm show \
  --resource-group "$RG_NAME" \
  --name "$VM_NAME" \
  --query "id" \
  -o tsv 2>/dev/null || echo "")

if [ -z "$VM_EXISTS" ]; then
  echo "⚠️  VM não encontrada: $VM_NAME"
  echo "   Pode já ter sido destruída"
  exit 0
fi

# Verificar status atual
VM_STATUS=$(az vm show \
  --resource-group "$RG_NAME" \
  --name "$VM_NAME" \
  --show-details \
  --query "powerState" \
  -o tsv 2>/dev/null || echo "Unknown")

echo "Status atual da VM: $VM_STATUS"

if [ "$DESTROY_MODE" == "delete" ]; then
  # Destruir VM completamente
  echo ""
  echo "⚠️  DESTRUINDO VM (modo delete)..."
  echo "   Isso vai remover a VM permanentemente!"
  
  # Desligar primeiro (se estiver rodando)
  if [ "$VM_STATUS" == "VM running" ]; then
    echo "Desligando VM..."
    az vm deallocate \
      --resource-group "$RG_NAME" \
      --name "$VM_NAME" \
      --no-wait
  fi

  # Aguardar desligar
  echo "Aguardando VM desligar..."
  MAX_WAIT=300  # 5 minutos
  WAIT_COUNT=0
  SLEEP_INTERVAL=10
  
  while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    CURRENT_STATUS=$(az vm show \
      --resource-group "$RG_NAME" \
      --name "$VM_NAME" \
      --show-details \
      --query "powerState" \
      -o tsv 2>/dev/null || echo "Unknown")
    
    if [ "$CURRENT_STATUS" != "VM running" ]; then
      echo "✅ VM desligada (Status: $CURRENT_STATUS)"
      break
    else
      WAIT_COUNT=$((WAIT_COUNT + SLEEP_INTERVAL))
      echo "⏳ Aguardando VM desligar... (Status: $CURRENT_STATUS, aguardado: ${WAIT_COUNT}s/${MAX_WAIT}s)"
      sleep $SLEEP_INTERVAL
    fi
  done

  # Deletar VM
  echo "Deletando VM..."
  az vm delete \
    --resource-group "$RG_NAME" \
    --name "$VM_NAME" \
    --yes \
    --no-wait

  echo ""
  echo "=========================================="
  echo "✅ VM destruída completamente!"
  echo "=========================================="
  echo "⚠️  Para recriar, execute 'terraform apply'"
  echo ""

else
  # Apenas desligar (deallocate) - mantém recursos mas para de cobrar compute
  echo ""
  echo "Desligando VM (modo deallocate)..."
  echo "   VM será mantida mas não cobrará custos de compute"
  
  if [ "$VM_STATUS" == "VM running" ]; then
    az vm deallocate \
      --resource-group "$RG_NAME" \
      --name "$VM_NAME" \
      --no-wait

    echo "Aguardando VM desligar..."
    MAX_WAIT=300  # 5 minutos
    WAIT_COUNT=0
    SLEEP_INTERVAL=10
    
    while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
      CURRENT_STATUS=$(az vm show \
        --resource-group "$RG_NAME" \
        --name "$VM_NAME" \
        --show-details \
        --query "powerState" \
        -o tsv 2>/dev/null || echo "Unknown")
      
      if [ "$CURRENT_STATUS" != "VM running" ]; then
        echo "✅ VM desligada (Status: $CURRENT_STATUS)"
        break
      else
        WAIT_COUNT=$((WAIT_COUNT + SLEEP_INTERVAL))
        echo "⏳ Aguardando VM desligar... (Status: $CURRENT_STATUS, aguardado: ${WAIT_COUNT}s/${MAX_WAIT}s)"
        sleep $SLEEP_INTERVAL
      fi
    done
    
    if [ "$CURRENT_STATUS" == "VM running" ]; then
      echo "⚠️  VM ainda está rodando após ${MAX_WAIT}s. Continuando mesmo assim..."
    fi

    echo ""
    echo "=========================================="
    echo "✅ VM desligada (deallocated)!"
    echo "=========================================="
    echo "VM ainda existe mas não está consumindo recursos de compute"
    echo "Para iniciar novamente, execute: az vm start -g $RG_NAME -n $VM_NAME"
    echo ""
  else
    echo "✅ VM já está desligada"
  fi
fi

