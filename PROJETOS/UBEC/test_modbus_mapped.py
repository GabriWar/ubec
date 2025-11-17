#!/usr/bin/env python3
"""
Script para ler e mostrar valores Modbus com nomes das variáveis
"""

from pymodbus.client import ModbusTcpClient
import sys

# Mapeamento de endereços para nomes de variáveis
MEMORY_MAP = {
    # Temperaturas (MW36-39)
    36: "Temperatura Ambiente",
    37: "Temperatura Quadro Elétrico",
    38: "Temperatura Módulo FV",
    39: "Temperatura Transformador",

    # Valores intermediários de temperatura (MW20-35)
    20: "IW1.0 - Entrada Analógica 1 (raw)",
    21: "IW1.1 - Entrada Analógica 2 (raw)",
    22: "MW22 - Temp dividido por 10",
    23: "MW23 - Temp dividido por 10",
    24: "MW24 - Temp dividido por 10",
    25: "MW25 - Temp dividido por 10",

    # Saídas digitais (MW200-209) - mapeamento de %M200-209
    200: "M200 - Comunicação OK",
    201: "M201 - Usina Gerando",
    202: "M202 - Falha",
    203: "M203 - Alarme",
    204: "M204 - Emergência Inversores",
    205: "M205 - Reset Rasp",
    206: "M206 - Reset Link 3G",
    207: "M207 - Reserva 1",
    208: "M208 - Reserva 2",
    209: "M209 - Reserva 3",

    # Entradas digitais (MW100-113) - mapeamento de %M100-113
    100: "M100 - DJ Geral Aberto",
    101: "M101 - DJ Geral Fechado",
    102: "M102 - Reserva I02",
    103: "M103 - Reserva I03",
    104: "M104 - Reserva I04",
    105: "M105 - Reserva I05",
    106: "M106 - Reserva I06",
    107: "M107 - Reserva I07",
    108: "M108 - Reserva I08",
    109: "M109 - Reserva I09",
    110: "M110 - Serviço Auxiliar",
    111: "M111 - Botão Close",
    112: "M112 - Botão Trip",
    113: "M113 - Botão Emergência",

    # Novos endereços mapeados (MW500-513) - cópia das entradas
    500: "MW500 -> M100 - DJ Geral Aberto",
    501: "MW501 -> M101 - DJ Geral Fechado",
    502: "MW502 -> M102 - Reserva I02",
    503: "MW503 -> M103 - Reserva I03",
    504: "MW504 -> M104 - Reserva I04",
    505: "MW505 -> M105 - Reserva I05",
    506: "MW506 -> M106 - Reserva I06",
    507: "MW507 -> M107 - Reserva I07",
    508: "MW508 -> M108 - Reserva I08",
    509: "MW509 -> M109 - Reserva I09",
    510: "MW510 -> M110 - Serviço Auxiliar",
    511: "MW511 -> M111 - Botão Close",
    512: "MW512 -> M112 - Botão Trip",
    513: "MW513 -> M113 - Botão Emergência",

    # Novos endereços mapeados (MW600-609) - cópia das saídas
    600: "MW600 -> M200 - Comunicação OK",
    601: "MW601 -> M201 - Usina Gerando",
    602: "MW602 -> M202 - Falha",
    603: "MW603 -> M203 - Alarme",
    604: "MW604 -> M204 - Emergência Inversores",
    605: "MW605 -> M205 - Reset Rasp",
    606: "MW606 -> M206 - Reset Link 3G",
    607: "MW607 -> M207 - Reserva 1",
    608: "MW608 -> M208 - Reserva 2",
    609: "MW609 -> M209 - Reserva 3",
}

# Conectar ao simulador
client = ModbusTcpClient('127.0.0.1', port=502)

if not client.connect():
    print("❌ Erro: Não conseguiu conectar ao simulador na porta 502")
    sys.exit(1)

print("✓ Conectado ao simulador Modbus TCP em 127.0.0.1:502\n")

# Grupos para leitura
groups = [
    ("TEMPERATURAS", 36, 4),
    ("VALORES INTERMEDIÁRIOS TEMP", 20, 6),
    ("ENTRADAS DIGITAIS (M100-113)", 100, 14),
    ("SAÍDAS DIGITAIS (M200-209)", 200, 10),
    ("ENTRADAS MAPEADAS (MW500-513)", 500, 14),
    ("SAÍDAS MAPEADAS (MW600-609)", 600, 10),
]

for group_name, start_addr, qty in groups:
    print("=" * 80)
    print(f"{group_name}")
    print("=" * 80)

    try:
        result = client.read_holding_registers(address=start_addr, count=qty)

        if hasattr(result, 'registers'):
            for i, val in enumerate(result.registers):
                addr = start_addr + i
                var_name = MEMORY_MAP.get(addr, f"MW{addr}")

                if val != 0:
                    print(f"  MW{addr:3d} = {val:5d} (0x{val:04X})  *  {var_name}")
                else:
                    print(f"  MW{addr:3d} = {val:5d}              {var_name}")
        else:
            print(f"  ❌ ERRO na leitura")

    except Exception as e:
        print(f"  ❌ EXCEÇÃO: {e}")

    print()

print("\n" + "=" * 80)
print("LEGENDA:")
print("=" * 80)
print("  * = Valor diferente de zero")
print("  MW = Memory Word (Holding Register)")
print("  M = Memory Bit (Coil)")
print("=" * 80)

client.close()
