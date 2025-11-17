#!/usr/bin/env python3
"""
Script para ESCREVER valores de teste nos registros Modbus
"""

from pymodbus.client import ModbusTcpClient
import sys

client = ModbusTcpClient('127.0.0.1', port=502)

if not client.connect():
    print("❌ Erro: Não conseguiu conectar ao simulador")
    sys.exit(1)

print("✓ Conectado ao simulador Modbus TCP\n")

# Escrever valores de teste
print("Escrevendo valores de teste...")

# MW500-513 (entradas simuladas)
test_inputs = [1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 1]  # 14 valores
result = client.write_registers(address=500, values=test_inputs)
if not result.isError():
    print(f"✓ MW500-513 (Entradas): escritos {len(test_inputs)} valores")
else:
    print(f"❌ Erro ao escrever MW500-513: {result}")

# MW600-609 (saídas simuladas)
test_outputs = [1, 1, 0, 0, 0, 0, 0, 0, 0, 0]  # 10 valores
result = client.write_registers(address=600, values=test_outputs)
if not result.isError():
    print(f"✓ MW600-609 (Saídas): escritos {len(test_outputs)} valores")
else:
    print(f"❌ Erro ao escrever MW600-609: {result}")

print("\nVerificando valores escritos...")

# Ler de volta
result = client.read_holding_registers(address=500, count=14)
if hasattr(result, 'registers'):
    print(f"\nMW500-513 (Entradas):")
    for i, val in enumerate(result.registers):
        if val != 0:
            print(f"  MW{500+i} = {val} *")

result = client.read_holding_registers(address=600, count=10)
if hasattr(result, 'registers'):
    print(f"\nMW600-609 (Saídas):")
    for i, val in enumerate(result.registers):
        if val != 0:
            print(f"  MW{600+i} = {val} *")

print("\n✓ Valores de teste escritos! Agora teste o Node-RED.")

client.close()
