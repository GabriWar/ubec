#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

get_items() {
  local current_dir="$1"
  local items=()
  
  # Lista pastas primeiro
  while IFS= read -r -d '' dir; do
    items+=("$dir")
  done < <(find "$current_dir" -mindepth 1 -maxdepth 1 -type d -print0 2>/dev/null | sort -z)
  
  # Lista scripts executáveis
  while IFS= read -r -d '' script; do
    items+=("$script")
  done < <(find "$current_dir" -mindepth 1 -maxdepth 1 -type f -executable -print0 2>/dev/null | sort -z)
  
  printf '%s\n' "${items[@]}"
}

show_menu() {
  local current_dir="$1"
  local items=()
  
  clear
  echo "======================"
  echo "        MENU"
  echo "======================"
  local rel_path="${current_dir#$SCRIPT_DIR/}"
  if [ "$rel_path" = "$current_dir" ]; then
    rel_path="."
  fi
  echo "Diretório: $rel_path"
  echo ""
  
  readarray -t items < <(get_items "$current_dir")
  
  local idx=1
  for item in "${items[@]}"; do
    if [ -d "$item" ]; then
      printf "%d) %s/\n" "$idx" "$(basename "$item")"
    else
      printf "%d) %s\n" "$idx" "$(basename "$item")"
    fi
    ((idx++))
  done
  
  echo ""
  if [ "$current_dir" != "$SCRIPT_DIR" ]; then
    echo "0) Voltar"
  else
    echo "0) Sair"
  fi
}

navigate_menu() {
  local current_dir="${1:-$SCRIPT_DIR}"
  
  while true; do
    local items=()
    readarray -t items < <(get_items "$current_dir")
    
    show_menu "$current_dir"
    
    read -rp "Escolha uma opção: " choice
    
    if [ "$choice" = "0" ]; then
      if [ "$current_dir" != "$SCRIPT_DIR" ]; then
        # Voltar para o diretório pai - retorna do loop atual
        return 0
      else
        echo "Saindo..."
        exit 0
      fi
    fi
    
    if ! [[ "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -lt 1 ] || [ "$choice" -gt "${#items[@]}" ]; then
      echo "Opção inválida!"
      sleep 1
      continue
    fi
    
    local selected="${items[$((choice-1))]}"
    
    if [ -d "$selected" ]; then
      # É uma pasta, navega para ela (chama recursivamente)
      navigate_menu "$selected"
      # Quando retorna do submenu, continua o loop atual
    elif [ -f "$selected" ] && [ -x "$selected" ]; then
      # É um script executável, executa
      echo "Executando: $selected"
      echo ""
      "$selected"
      echo ""
      read -rp "Pressione Enter para voltar ao menu..."
    fi
  done
}

main() {
  navigate_menu "$SCRIPT_DIR"
}

main
