#!/usr/bin/env python3
"""
Script para adicionar rungs de RESET para corrigir bug Modbus
Adiciona novos rungs com LDN e [ %MWxxx := 0 ]
"""

import xml.etree.ElementTree as ET
import sys
from pathlib import Path

def backup_file(filepath):
    """Cria backup do arquivo original"""
    backup_path = filepath.with_suffix('.smbp.backup3')
    import shutil
    shutil.copy2(filepath, backup_path)
    print(f"✓ Backup criado: {backup_path}")
    return backup_path

def create_reset_rung(source_var, mw_register, rung_name):
    """
    Cria um novo RungEntity com LDN e [ %MWxxx := 0 ]
    """
    rung = ET.Element('RungEntity')
    
    # ==================== LadderElements ====================
    ladder_elements = ET.SubElement(rung, 'LadderElements')
    
    # Contato negado (LDN)
    contact = ET.SubElement(ladder_elements, 'LadderEntity')
    ET.SubElement(contact, 'ElementType').text = 'NegatedContact'
    ET.SubElement(contact, 'Descriptor').text = source_var
    ET.SubElement(contact, 'Comment')
    if not source_var.startswith('%'):
        ET.SubElement(contact, 'Symbol').text = source_var
    ET.SubElement(contact, 'Row').text = '0'
    ET.SubElement(contact, 'Column').text = '0'
    ET.SubElement(contact, 'ChosenConnection').text = 'Left, Right'
    
    # Linhas (colunas 1-8)
    for col in range(1, 9):
        line = ET.SubElement(ladder_elements, 'LadderEntity')
        ET.SubElement(line, 'ElementType').text = 'Line'
        ET.SubElement(line, 'Descriptor')
        ET.SubElement(line, 'Row').text = '0'
        ET.SubElement(line, 'Column').text = str(col)
        ET.SubElement(line, 'ChosenConnection').text = 'Left, Right'
    
    # Operação [ %MWxxx := 0 ]
    operation = ET.SubElement(ladder_elements, 'LadderEntity')
    ET.SubElement(operation, 'ElementType').text = 'Operation'
    ET.SubElement(operation, 'OperationExpression').text = f'{mw_register} := 0'
    ET.SubElement(operation, 'Row').text = '0'
    ET.SubElement(operation, 'Column').text = '9'
    ET.SubElement(operation, 'ChosenConnection').text = 'Left, Right'
    
    # ==================== InstructionLines ====================
    instruction_lines = ET.SubElement(rung, 'InstructionLines')
    
    # Linha 1: LDN
    instr1 = ET.SubElement(instruction_lines, 'InstructionLineEntity')
    ET.SubElement(instr1, 'InstructionLine').text = f'LDN   {source_var}'
    ET.SubElement(instr1, 'Comment')
    
    # Linha 2: [ %MWxxx := 0 ]
    instr2 = ET.SubElement(instruction_lines, 'InstructionLineEntity')
    ET.SubElement(instr2, 'InstructionLine').text = f'[ {mw_register} := 0 ]'
    ET.SubElement(instr2, 'Comment')
    
    # ==================== Metadados ====================
    ET.SubElement(rung, 'Name').text = f'{rung_name} - RESET'
    ET.SubElement(rung, 'MainComment')
    ET.SubElement(rung, 'Label')
    ET.SubElement(rung, 'IsLadderSelected').text = 'true'
    
    return rung

def find_source_variable_from_rung(rung):
    """
    Encontra a variável de origem de um rung analisando InstructionLines
    """
    instruction_lines = rung.find('InstructionLines')
    if instruction_lines is None:
        return None
    
    for entity in instruction_lines.findall('InstructionLineEntity'):
        instruction_elem = entity.find('InstructionLine')
        if instruction_elem is not None:
            instruction = instruction_elem.text
            # Procura por LD ou ST
            if instruction.startswith('LD ') and not instruction.startswith('LDN'):
                parts = instruction.split()
                if len(parts) >= 2:
                    return parts[1]
            elif instruction.startswith('ST '):
                # Se encontrar ST, continua procurando o LD anterior
                continue
    
    return None

def add_reset_rungs(input_file, output_file=None):
    """
    Adiciona rungs de RESET após cada rung que contém [ %MWxxx := 1 ]
    """
    input_path = Path(input_file)
    
    if not input_path.exists():
        print(f"❌ Arquivo não encontrado: {input_file}")
        return False
    
    # Cria backup
    backup_file(input_path)
    
    # Lê o arquivo XML
    print(f"\n📖 Lendo arquivo: {input_file}")
    try:
        tree = ET.parse(input_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"❌ Erro ao ler XML: {e}")
        return False
    
    print("\n🔍 Procurando rungs com [ %MWxxx := 1 ] e adicionando RESETs...\n")
    
    rungs_added = 0
    
    # Mapeamento de MWs para variáveis (para casos onde não consegue detectar)
    mw_to_var = {
        '%MW500': '%I0.0',
        '%MW501': '%I0.1',
        '%MW510': '%I0.10',
        '%MW511': '%I0.11',
        '%MW512': '%I0.12',
        '%MW513': '%I0.13',
        '%MW600': '%M0',
        '%MW601': '%M1',
        '%MW602': '%M2',
        '%MW603': '%M3',
        '%MW604': '%Q0.4',
        '%MW606': '%Q0.6',
    }
    
    # Processa todas as seções
    for section in root.findall('.//ProgramOrganizationUnits'):
        rungs_container = section.find('Rungs')
        if rungs_container is None:
            continue
        
        rungs = list(rungs_container.findall('RungEntity'))
        new_rungs_to_add = []
        
        for idx, rung in enumerate(rungs):
            rung_name = rung.find('Name')
            if rung_name is None:
                continue
            
            name = rung_name.text
            
            # Verifica se o rung tem [ %MWxxx := 1 ]
            instruction_lines = rung.find('InstructionLines')
            if instruction_lines is None:
                continue
            
            mw_register = None
            
            for entity in instruction_lines.findall('InstructionLineEntity'):
                instruction_elem = entity.find('InstructionLine')
                if instruction_elem is not None:
                    instruction = instruction_elem.text
                    # Procura por [ %MW5xx ou %MW6xx := 1 ]
                    import re
                    match = re.search(r'\[\s*(%MW[56]\d{2})\s*:=\s*1\s*\]', instruction)
                    if match:
                        mw_register = match.group(1)
                        break
            
            if mw_register:
                # Encontra variável de origem
                source_var = find_source_variable_from_rung(rung)
                
                # Se não encontrou, usa o mapeamento
                if not source_var or not source_var.startswith('%'):
                    source_var = mw_to_var.get(mw_register)
                
                if source_var:
                    print(f"🔧 Rung: {name}")
                    print(f"   MW: {mw_register}")
                    print(f"   Variável: {source_var}")
                    
                    # Cria novo rung de RESET
                    new_rung = create_reset_rung(source_var, mw_register, name)
                    
                    # Adiciona à lista para inserir depois (posição após o rung atual)
                    new_rungs_to_add.append((idx + 1 + len(new_rungs_to_add), new_rung))
                    
                    rungs_added += 1
                    print(f"   ✅ Rung de RESET criado!\n")
                else:
                    print(f"⚠️  Não foi possível determinar variável para {mw_register} em {name}\n")
        
        # Adiciona os novos rungs nas posições corretas
        for position, new_rung in reversed(new_rungs_to_add):
            rungs_container.insert(position, new_rung)
    
    # Salva o arquivo corrigido
    if output_file is None:
        output_file = input_path.with_stem(input_path.stem + '_COM_RESETS')
    
    output_path = Path(output_file)
    
    print(f"💾 Salvando arquivo corrigido: {output_path}")
    
    # Salva com formatação
    tree.write(output_path, encoding='utf-8', xml_declaration=True)
    
    print(f"\n{'='*80}")
    print(f"✅ CORREÇÃO CONCLUÍDA!")
    print(f"{'='*80}")
    print(f"🆕 Total de rungs RESET adicionados: {rungs_added}")
    print(f"📁 Arquivo original (backup): {input_path.with_suffix('.smbp.backup3')}")
    print(f"📁 Arquivo corrigido: {output_path}")
    print(f"{'='*80}\n")
    
    if rungs_added > 0:
        print("⚠️  PRÓXIMOS PASSOS:")
        print("   1. Feche o SoMachine Basic se estiver aberto")
        print("   2. Abra o novo arquivo no SoMachine Basic")
        print("   3. Compile o projeto (F7)")
        print("   4. Verifique se não há erros")
        print("   5. Faça download para o CLP")
        print()
    
    return True

if __name__ == '__main__':
    print("\n" + "="*80)
    print("🔧 ADICIONADOR AUTOMÁTICO DE RUNGS DE RESET - PROJETO UBEC")
    print("="*80 + "\n")
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = 'correto.smbp'
    
    output_file = None
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    success = add_reset_rungs(input_file, output_file)
    
    sys.exit(0 if success else 1)

