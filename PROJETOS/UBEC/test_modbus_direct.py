#!/usr/bin/env python3
"""
Script para testar diretamente quais endereços Modbus respondem no simulador
"""

from pymodbus.client import ModbusTcpClient
import sys

# Conectar ao simulador
client = ModbusTcpClient('127.0.0.1', port=502)

if not client.connect():
    print("❌ Erro: Não conseguiu conectar ao simulador na porta 502")
    sys.exit(1)

print("✓ Conectado ao simulador Modbus TCP em 127.0.0.1:502\n")

# Teste rápido de temperaturas
print("="*60)
print("TESTE RÁPIDO: Lendo MW36-39 (Temperaturas) 5 vezes")
print("="*60)
for i in range(5):
    try:
        result = client.read_holding_registers(address=36, count=4)
        if hasattr(result, 'registers'):
            print(f"Leitura {i+1}: MW36={result.registers[0]}, MW37={result.registers[1]}, MW38={result.registers[2]}, MW39={result.registers[3]}")
        else:
            print(f"Leitura {i+1}: ERRO")
    except Exception as e:
        print(f"Leitura {i+1}: EXCEÇÃO - {e}")
    import time
    time.sleep(0.5)

print("\n" + "="*60)
print("SCAN COMPLETO DE TODOS OS ENDEREÇOS")
print("="*60 + "\n")

# Testar leituras
tests = [
    ("Temperaturas (MW36-39)", 3, 36, 4),
    ("MW0-19", 3, 0, 20),
    ("MW20-39", 3, 20, 20),
    ("MW40-59", 3, 40, 20),
    ("MW60-79", 3, 60, 20),
    ("MW80-99", 3, 80, 20),
    ("MW100-119", 3, 100, 20),
    ("MW120-139", 3, 120, 20),
    ("MW140-159", 3, 140, 20),
    ("MW160-179", 3, 160, 20),
    ("MW180-199", 3, 180, 20),
    ("MW200-219", 3, 200, 20),
    ("MW500-519", 3, 500, 20),
    ("MW600-619", 3, 600, 20),
]

print("Testando leituras Modbus FC3 (Holding Registers):\n")

for name, fc, addr, qty in tests:
    try:
        # Tentar diferentes sintaxes de pymodbus
        result = None

        # Tentar versão 3.x
        try:
            result = client.read_holding_registers(address=addr, count=qty)
        except:
            pass

        # Tentar versão 2.x
        if result is None:
            try:
                result = client.read_holding_registers(addr, qty)
            except:
                pass

        # Tentar versão antiga
        if result is None:
            result = client.read_holding_registers(addr, count=qty)

        if hasattr(result, 'isError') and result.isError():
            print(f"❌ {name}: ERRO - {result}")
        elif hasattr(result, 'registers'):
            print(f"✓ {name}: OK")
            # Mostrar todos os valores
            print(f"   Valores lidos:")
            for i, val in enumerate(result.registers):
                reg_addr = addr + i
                if val != 0:
                    print(f"      MW{reg_addr:3d} = {val:5d} (0x{val:04X}) *")
                else:
                    print(f"      MW{reg_addr:3d} = {val:5d}")
            print()
        else:
            print(f"❌ {name}: Resposta inválida - {type(result)}")

    except Exception as e:
        print(f"❌ {name}: EXCEÇÃO - {e}")

print("\n" + "="*60)
print("CONCLUSÃO:")
print("="*60)
print("Os endereços que responderam OK estão disponíveis no simulador.")
print("Os que deram ERRO não existem ou não estão configurados no Modbus.")
print("="*60)

client.close()
