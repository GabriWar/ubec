#!/usr/bin/env bash

set -euo pipefail

SSID="mtz"
PASSWORD="mtz123mtz"
CONNECTION_NAME="mtz-hotspot"

require_nmcli() {
  if ! command -v nmcli >/dev/null 2>&1; then
    echo "Erro: nmcli não encontrado. Instale o NetworkManager."
    exit 1
  fi
}

main() {
  clear
  echo "======================"
  echo "   INICIAR HOTSPOT"
  echo "======================"
  echo ""

  require_nmcli

  local interface="wlan0"

  # Verifica se a interface existe
  if ! nmcli -t -f DEVICE device status | grep -q "^${interface}$"; then
    echo "Erro: Interface $interface não encontrada." >&2
    read -rp "Pressione Enter para voltar..."
    return 1
  fi

  echo "Interface Wi-Fi: $interface" >&2
  echo "SSID: $SSID" >&2
  echo ""

  # Verifica se a conexão já existe
  if nmcli -t -f NAME connection show | grep -q "^${CONNECTION_NAME}$"; then
    echo "Conexão hotspot já existe. Ativando..." >&2
    if nmcli connection up id "${CONNECTION_NAME}" >/dev/null 2>&1; then
      echo "✓ Hotspot iniciado com sucesso!" >&2
      echo ""
      echo "SSID: $SSID"
      echo "Senha: $PASSWORD"
      echo ""
      read -rp "Pressione Enter para voltar..."
      return 0
    else
      echo "Erro ao ativar conexão existente. Tentando recriar..." >&2
      nmcli connection delete id "${CONNECTION_NAME}" >/dev/null 2>&1 || true
    fi
  fi

  echo "Criando e iniciando hotspot..." >&2
  if nmcli connection add type wifi ifname "$interface" con-name "${CONNECTION_NAME}" ssid "$SSID" \
    802-11-wireless.mode ap \
    802-11-wireless-security.key-mgmt wpa-psk \
    802-11-wireless-security.psk "$PASSWORD" \
    ipv4.method shared >/dev/null 2>&1; then
    
    echo "Conexão criada. Ativando..." >&2
    sleep 1
    
    if nmcli connection up id "${CONNECTION_NAME}" >/dev/null 2>&1; then
      echo "✓ Hotspot iniciado com sucesso!" >&2
      echo ""
      echo "SSID: $SSID"
      echo "Senha: $PASSWORD"
      echo ""
      read -rp "Pressione Enter para voltar..."
    else
      echo "Erro ao ativar o hotspot." >&2
      read -rp "Pressione Enter para voltar..."
      return 1
    fi
  else
    echo "Erro ao criar o hotspot." >&2
    read -rp "Pressione Enter para voltar..."
    return 1
  fi
}

main
