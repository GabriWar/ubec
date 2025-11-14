#!/usr/bin/env bash

set -euo pipefail

require_nmcli() {
  if ! command -v nmcli >/dev/null 2>&1; then
    echo "nmcli não encontrado. Instale o NetworkManager ou execute em um sistema compatível."
    read -rp "Pressione Enter para voltar..."
    return 1
  fi
  return 0
}

select_adapter() {
  mapfile -t adapters < <(nmcli -t -f DEVICE,TYPE,STATE device status | awk -F: '$2=="wifi"{print $1 ":" $3}')

  if [ "${#adapters[@]}" -eq 0 ]; then
    echo "Nenhum adaptador Wi-Fi encontrado." >&2
    printf "Pressione Enter para voltar..." >&2
    read -r
    return 1
  fi

  echo "Adaptadores Wi-Fi disponíveis:" >&2
  local idx=1
  for entry in "${adapters[@]}"; do
    local dev state
    IFS=":" read -r dev state <<<"$entry"
    printf "%d) %s (%s)\n" "$idx" "$dev" "$state" >&2
    ((idx++))
  done

  printf "Selecione o adaptador: " >&2
  read -r choice
  if ! [[ "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -lt 1 ] || [ "$choice" -gt "${#adapters[@]}" ]; then
    echo "Escolha inválida." >&2
    sleep 1
    return 1
  fi

  IFS=":" read -r selected_adapter _ <<<"${adapters[$((choice-1))]}"
  echo "$selected_adapter"
}

select_network() {
  local adapter="$1"
  echo "Buscando redes com $adapter..." >&2
  nmcli device wifi rescan ifname "$adapter" >/dev/null 2>&1 || true

  mapfile -t networks < <(nmcli -t -f SSID,BSSID,SIGNAL,SECURITY device wifi list ifname "$adapter" | awk -F: 'length($1)>0 {print $1 ":" $2 ":" $3 ":" $4}')

  if [ "${#networks[@]}" -eq 0 ]; then
    echo "Nenhuma rede encontrada." >&2
    printf "Pressione Enter para voltar..." >&2
    read -r
    return 1
  fi

  echo "Redes disponíveis:" >&2
  local idx=1
  for entry in "${networks[@]}"; do
    IFS=":" read -r ssid bssid signal security <<<"$entry"
    printf "%d) %s (signal: %s, security: %s)\n" "$idx" "$ssid" "$signal" "${security:-OPEN}" >&2
    ((idx++))
  done

  printf "Selecione a rede: " >&2
  read -r choice
  if ! [[ "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -lt 1 ] || [ "$choice" -gt "${#networks[@]}" ]; then
    echo "Escolha inválida." >&2
    sleep 1
    return 1
  fi

  echo "${networks[$((choice-1))]}"
}

main() {
  clear
  echo "======================"
  echo "   CONECTAR WI-FI"
  echo "======================"
  echo ""

  require_nmcli || return

  local adapter
  adapter="$(select_adapter)" || return

  local network_entry
  network_entry="$(select_network "$adapter")" || return

  local ssid _signal security
  IFS=":" read -r ssid _bssid _signal security <<<"$network_entry"

  if [ -z "$ssid" ]; then
    echo "SSID inválido."
    sleep 1
    return
  fi

  local password_args=()
  if [ -n "$security" ] && [ "$security" != "--" ] && [ "$security" != "NONE" ]; then
    read -rsp "Senha para $ssid: " wifi_pass
    echo
    password_args=(password "$wifi_pass")
  fi

  echo "Conectando $adapter em $ssid..."
  if nmcli device wifi connect "$ssid" ifname "$adapter" "${password_args[@]}" >/dev/null 2>&1; then
    echo "Conectado com sucesso!"
  else
    echo "Falha ao conectar."
  fi
  read -rp "Pressione Enter para voltar..."
}

main
