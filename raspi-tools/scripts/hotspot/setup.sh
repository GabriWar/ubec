#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="raspi-hotspot"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

require_nmcli() {
  if ! command -v nmcli >/dev/null 2>&1; then
    echo "Erro: nmcli não encontrado. Instale o NetworkManager."
    exit 1
  fi
}

require_root() {
  if [ "$EUID" -ne 0 ]; then
    echo "Erro: Este script precisa ser executado como root (use sudo)."
    exit 1
  fi
}

list_wifi_interfaces() {
  mapfile -t interfaces < <(nmcli -t -f DEVICE,TYPE device status | awk -F: '$2=="wifi"{print $1}')

  if [ "${#interfaces[@]}" -eq 0 ]; then
    echo "Nenhuma interface Wi-Fi encontrada." >&2
    return 1
  fi

  echo "Interfaces Wi-Fi disponíveis:" >&2
  local idx=1
  for iface in "${interfaces[@]}"; do
    printf "%d) %s\n" "$idx" "$iface" >&2
    ((idx++))
  done

  printf "Selecione a interface: " >&2
  read -r choice

  if ! [[ "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -lt 1 ] || [ "$choice" -gt "${#interfaces[@]}" ]; then
    echo "Escolha inválida." >&2
    return 1
  fi

  echo "${interfaces[$((choice-1))]}"
}

get_ssid() {
  while true; do
    printf "Nome do hotspot (SSID): " >&2
    read -r ssid
    if [ -z "$ssid" ]; then
      echo "O nome não pode estar vazio." >&2
      continue
    fi
    if [ ${#ssid} -gt 32 ]; then
      echo "O nome deve ter no máximo 32 caracteres." >&2
      continue
    fi
    echo "$ssid"
    return
  done
}

get_password() {
  while true; do
    printf "Senha do hotspot (mínimo 8 caracteres): " >&2
    read -rs password
    echo >&2
    if [ ${#password} -lt 8 ]; then
      echo "A senha deve ter pelo menos 8 caracteres." >&2
      continue
    fi
    printf "Confirme a senha: " >&2
    read -rs password_confirm
    echo >&2
    if [ "$password" != "$password_confirm" ]; then
      echo "As senhas não coincidem." >&2
      continue
    fi
    echo "$password"
    return
  done
}

create_service() {
  local interface="$1"
  local ssid="$2"
  local password="$3"

  cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Raspberry Pi Hotspot Service
After=network-online.target NetworkManager.service
Wants=network-online.target NetworkManager.service
Before=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/bin/bash -c 'until /usr/bin/nmcli -t -f STATE general status | grep -q "^connected\\|^connecting"; do sleep 1; done; /usr/bin/nmcli connection up id ${SERVICE_NAME} 2>/dev/null || /usr/bin/nmcli connection add type wifi ifname ${interface} con-name ${SERVICE_NAME} ssid ${ssid} 802-11-wireless.mode ap 802-11-wireless-security.key-mgmt wpa-psk 802-11-wireless-security.psk ${password} ipv4.method shared && /usr/bin/nmcli connection up id ${SERVICE_NAME}'
ExecStop=/usr/bin/nmcli connection down id ${SERVICE_NAME}
Restart=on-failure
RestartSec=10
TimeoutStartSec=60

[Install]
WantedBy=multi-user.target
EOF

  echo "Serviço criado em $SERVICE_FILE"
}

main() {
  clear
  echo "======================"
  echo "   SETUP HOTSPOT"
  echo "======================"
  echo ""

  require_nmcli
  require_root

  # Remove conexão existente se houver
  if nmcli -t -f NAME connection show | grep -q "^${SERVICE_NAME}$"; then
    echo "Removendo conexão existente '${SERVICE_NAME}'..." >&2
    nmcli connection delete id "${SERVICE_NAME}" >/dev/null 2>&1 || true
  fi

  # Remove serviço existente se houver
  if [ -f "$SERVICE_FILE" ]; then
    echo "Parando e removendo serviço existente..." >&2
    systemctl stop "${SERVICE_NAME}" >/dev/null 2>&1 || true
    systemctl disable "${SERVICE_NAME}" >/dev/null 2>&1 || true
    rm -f "$SERVICE_FILE"
    systemctl daemon-reload
  fi

  local interface
  interface="$(list_wifi_interfaces)" || exit 1

  local ssid
  ssid="$(get_ssid)"

  local password
  password="$(get_password)"

  echo ""
  echo "Criando conexão hotspot..." >&2
  nmcli connection add type wifi ifname "$interface" con-name "${SERVICE_NAME}" ssid "$ssid" \
    802-11-wireless.mode ap \
    802-11-wireless-security.key-mgmt wpa-psk \
    802-11-wireless-security.psk "$password" \
    ipv4.method shared >/dev/null 2>&1

  echo "Criando serviço systemd..." >&2
  create_service "$interface" "$ssid" "$password"

  echo "Recarregando systemd..." >&2
  systemctl daemon-reload

  echo "Habilitando serviço para iniciar no boot..." >&2
  systemctl enable "${SERVICE_NAME}"

  # Verificar se foi habilitado corretamente
  if systemctl is-enabled "${SERVICE_NAME}" >/dev/null 2>&1; then
    echo "✓ Serviço habilitado para iniciar no boot" >&2
  else
    echo "⚠ Aviso: Não foi possível habilitar o serviço para iniciar no boot" >&2
  fi

  echo "Iniciando serviço..." >&2
  systemctl start "${SERVICE_NAME}"

  echo ""
  echo "======================"
  echo "Hotspot configurado com sucesso!"
  echo "======================"
  echo "Nome (SSID): $ssid"
  echo "Interface: $interface"
  echo "Serviço: ${SERVICE_NAME}"
  echo ""
  echo "Status do serviço:" >&2
  systemctl status "${SERVICE_NAME}" --no-pager -l || true
  echo ""
  echo "✓ O hotspot está configurado para iniciar automaticamente no boot do Raspberry Pi."
  echo ""
  if systemctl is-enabled "${SERVICE_NAME}" >/dev/null 2>&1; then
    echo "✓ Serviço habilitado: $(systemctl is-enabled ${SERVICE_NAME})"
  fi
  echo ""
  echo "Para gerenciar o serviço:"
  echo "  sudo systemctl status ${SERVICE_NAME}"
  echo "  sudo systemctl stop ${SERVICE_NAME}"
  echo "  sudo systemctl start ${SERVICE_NAME}"
  echo "  sudo systemctl restart ${SERVICE_NAME}"
  echo ""
  echo "Para verificar se está habilitado para iniciar no boot:"
  echo "  sudo systemctl is-enabled ${SERVICE_NAME}"
  echo ""
  read -rp "Pressione Enter para voltar..."
}

main
