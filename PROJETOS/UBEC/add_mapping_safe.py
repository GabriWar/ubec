#!/usr/bin/env python3
"""
Script SEGURO para adicionar mapeamento M100 -> MW500 (apenas 2 rungs de teste)
"""

import shutil
from datetime import datetime

# Backup
backup_file = "PROJETO2_com_modbus_backup_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".smbp"
shutil.copy("PROJETO2_com_modbus.smbp", backup_file)
print(f"✓ Backup criado: {backup_file}")

# Ler arquivo
with open("PROJETO2_com_modbus.smbp", 'r', encoding='utf-8') as f:
    content = f.read()

print("\nAdicionando 2 rungs de TESTE para M100 -> MW500...")

# Estrutura EXATA copiada do rung existente, apenas mudando os valores
rung_m100_set = """          <RungEntity>
            <LadderElements>
              <LadderEntity>
                <ElementType>NormalContact</ElementType>
                <Descriptor>%M100</Descriptor>
                <Comment />
                <Row>0</Row>
                <Column>0</Column>
                <ChosenConnection>Left, Right</ChosenConnection>
              </LadderEntity>
              <LadderEntity>
                <ElementType>Line</ElementType>
                <Descriptor />
                <Row>0</Row>
                <Column>1</Column>
                <ChosenConnection>Left, Right</ChosenConnection>
              </LadderEntity>
              <LadderEntity>
                <ElementType>Operation</ElementType>
                <OperationExpression>%MW500 := 1</OperationExpression>
                <Row>0</Row>
                <Column>2</Column>
                <ChosenConnection>Left</ChosenConnection>
              </LadderEntity>
            </LadderElements>
            <InstructionLines>
              <InstructionLineEntity>
                <InstructionLine>LD    %M100</InstructionLine>
                <Comment />
              </InstructionLineEntity>
              <InstructionLineEntity>
                <InstructionLine>[ %MW500 := 1 ]</InstructionLine>
                <Comment />
              </InstructionLineEntity>
            </InstructionLines>
            <Name>MODBUS MAP: M100 SET MW500</Name>
            <Label />
            <IsLadderSelected>true</IsLadderSelected>
          </RungEntity>
"""

rung_m100_reset = """          <RungEntity>
            <LadderElements>
              <LadderEntity>
                <ElementType>InvertedContact</ElementType>
                <Descriptor>%M100</Descriptor>
                <Comment />
                <Row>0</Row>
                <Column>0</Column>
                <ChosenConnection>Left, Right</ChosenConnection>
              </LadderEntity>
              <LadderEntity>
                <ElementType>Line</ElementType>
                <Descriptor />
                <Row>0</Row>
                <Column>1</Column>
                <ChosenConnection>Left, Right</ChosenConnection>
              </LadderEntity>
              <LadderEntity>
                <ElementType>Operation</ElementType>
                <OperationExpression>%MW500 := 0</OperationExpression>
                <Row>0</Row>
                <Column>2</Column>
                <ChosenConnection>Left</ChosenConnection>
              </LadderEntity>
            </LadderElements>
            <InstructionLines>
              <InstructionLineEntity>
                <InstructionLine>LDN   %M100</InstructionLine>
                <Comment />
              </InstructionLineEntity>
              <InstructionLineEntity>
                <InstructionLine>[ %MW500 := 0 ]</InstructionLine>
                <Comment />
              </InstructionLineEntity>
            </InstructionLines>
            <Name>MODBUS MAP: M100 RESET MW500</Name>
            <Label />
            <IsLadderSelected>true</IsLadderSelected>
          </RungEntity>
"""

# Encontrar onde inserir - procurar exatamente pelo fechamento da última rung
# A estrutura é:   </RungEntity>\n        </Rungs>
insert_marker = """          </RungEntity>
        </Rungs>"""

if insert_marker not in content:
    print("❌ Erro: Marcador de inserção não encontrado")
    print("Tentando com \\r\\n...")
    insert_marker = insert_marker.replace('\n', '\r\n')
    if insert_marker not in content:
        print("❌ Erro: Marcador não encontrado nem com \\r\\n")
        exit(1)

print("✓ Marcador de inserção encontrado")

# Inserir os 2 rungs ANTES do </Rungs>
new_content = content.replace(
    insert_marker,
    rung_m100_set + rung_m100_reset + insert_marker,
    1  # Apenas a primeira ocorrência
)

# Verificar se mudou
if len(new_content) == len(content):
    print("❌ Erro: Conteúdo não foi modificado!")
    exit(1)

print(f"✓ Arquivo cresceu de {len(content)} para {len(new_content)} bytes")

# Salvar
with open("PROJETO2_com_modbus.smbp", 'w', encoding='utf-8') as f:
    f.write(new_content)

print("\n" + "="*60)
print("✓ 2 RUNGS DE TESTE adicionados com sucesso!")
print("="*60)
print("\nMapeamento adicionado:")
print("  M100 -> MW500 (2 rungs: SET quando M100=1, RESET quando M100=0)")
print("\nPRÓXIMOS PASSOS:")
print("1. Abra PROJETO2_com_modbus.smbp no SoMachine")
print("2. Verifique se o projeto abre sem erros")
print("3. Veja se os 2 novos rungs aparecem no ladder")
print("4. Se funcionar, rodamos o script para adicionar TODOS os rungs")
print("="*60)
