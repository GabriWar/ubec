#!/usr/bin/env python3
"""
Script para corrigir o BUG de mapeamento Modbus no projeto UBEC
Converte instruções [ %MWxxx := 1 ] em duas operações (SET e RESET)
"""

import xml.etree.ElementTree as ET
import re
import sys
from pathlib import Path

def backup_file(filepath):
    """Cria backup do arquivo original"""
    backup_path = filepath.with_suffix('.smbp.backup')
    import shutil
    shutil.copy2(filepath, backup_path)
    print(f"✓ Backup criado: {backup_path}")
    return backup_path

def find_source_variable(instruction_lines, mw_line_index):
    """
    Encontra a variável de origem olhando as linhas anteriores
    Procura por LD ou ST antes da operação MW
    """
    for i in range(mw_line_index - 1, -1, -1):
        line = instruction_lines[i].find('InstructionLine').text
        
        # Procura por LD ou ST com variável
        if line.startswith('LD ') and not line.startswith('LDN'):
            var = line.split()[1]
            if var != '1' and '%' in var:
                return var
        elif line.startswith('ST '):
            var = line.split()[1]
            if '%' in var:
                return var
    
    return None

def fix_rung(rung):
    """
    Corrige um rung substituindo [ %MWxxx := 1 ] por duas operações
    """
    instruction_lines = rung.find('InstructionLines')
    if instruction_lines is None:
        return False
    
    entities = list(instruction_lines.findall('InstructionLineEntity'))
    modified = False
    
    for idx, entity in enumerate(entities):
        instruction_elem = entity.find('InstructionLine')
        if instruction_elem is None:
            continue
        
        instruction = instruction_elem.text
        
        # Procura por padrão [ %MWxxx := 1 ]
        match = re.match(r'\[\s*(%MW\d+)\s*:=\s*1\s*\]', instruction)
        if match:
            mw_register = match.group(1)
            
            # Encontra variável de origem
            source_var = find_source_variable(entities, idx)
            
            if source_var:
                print(f"  🔧 Corrigindo: {instruction}")
                print(f"     Variável origem: {source_var}")
                print(f"     Novo: LD {source_var} → [ {mw_register} := 1 ]")
                print(f"          LDN {source_var} → [ {mw_register} := 0 ]")
                
                # Modifica a instrução atual para adicionar LD antes
                instruction_elem.text = f"[ {mw_register} := 1 ]"
                
                # Cria nova linha com LD source_var ANTES da operação
                new_ld_entity = ET.Element('InstructionLineEntity')
                new_ld_line = ET.SubElement(new_ld_entity, 'InstructionLine')
                new_ld_line.text = f"LD    {source_var}"
                new_ld_comment = ET.SubElement(new_ld_entity, 'Comment')
                
                # Cria nova linha com LDN source_var
                new_ldn_entity = ET.Element('InstructionLineEntity')
                new_ldn_line = ET.SubElement(new_ldn_entity, 'InstructionLine')
                new_ldn_line.text = f"LDN   {source_var}"
                new_ldn_comment = ET.SubElement(new_ldn_entity, 'Comment')
                
                # Cria nova linha com [ %MWxxx := 0 ]
                new_reset_entity = ET.Element('InstructionLineEntity')
                new_reset_line = ET.SubElement(new_reset_entity, 'InstructionLine')
                new_reset_line.text = f"[ {mw_register} := 0 ]"
                new_reset_comment = ET.SubElement(new_reset_entity, 'Comment')
                
                # Insere as novas linhas na posição correta
                instruction_lines.insert(idx, new_ld_entity)
                instruction_lines.insert(idx + 2, new_ldn_entity)
                instruction_lines.insert(idx + 3, new_reset_entity)
                
                modified = True
                break  # Processa apenas uma correção por rung
    
    return modified

def fix_modbus_mapping(input_file, output_file=None):
    """
    Corrige o mapeamento Modbus no arquivo .smbp
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
    
    # Procura por todos os rungs
    print("\n🔍 Procurando rungs com bug de mapeamento Modbus...\n")
    
    rungs_fixed = 0
    total_rungs = 0
    
    for section in root.findall('.//ProgramOrganizationUnits'):
        section_name = section.find('Name')
        if section_name is not None and 'Mapeamento Modbus' in section_name.text:
            print(f"📍 Seção encontrada: {section_name.text}\n")
            
            rungs = section.find('Rungs')
            if rungs is not None:
                for rung in rungs.findall('RungEntity'):
                    total_rungs += 1
                    rung_name = rung.find('Name')
                    
                    if rung_name is not None and 'MAP MODBUS' in rung_name.text:
                        print(f"🔧 Analisando: {rung_name.text}")
                        
                        if fix_rung(rung):
                            rungs_fixed += 1
                            print(f"   ✅ Corrigido!\n")
                        else:
                            print(f"   ⏭️  Sem alterações necessárias\n")
    
    # Também corrige outros rungs que setam MW500-513 e MW600-609
    for rung in root.findall('.//RungEntity'):
        instruction_lines = rung.find('InstructionLines')
        if instruction_lines:
            for entity in instruction_lines.findall('InstructionLineEntity'):
                instruction_elem = entity.find('InstructionLine')
                if instruction_elem is not None:
                    instruction = instruction_elem.text
                    # Procura setagens de MW500-513 (inputs) e MW600-609 (outputs)
                    if re.search(r'\[\s*%MW[56]\d{2}\s*:=\s*1\s*\]', instruction):
                        rung_name = rung.find('Name')
                        if rung_name is not None and 'MAP MODBUS' not in rung_name.text:
                            print(f"🔧 Corrigindo rung adicional: {rung_name.text}")
                            if fix_rung(rung):
                                rungs_fixed += 1
                                print(f"   ✅ Corrigido!\n")
                            break  # Pula para próximo rung após corrigir
    
    # Salva o arquivo corrigido
    if output_file is None:
        output_file = input_path.with_stem(input_path.stem + '_CORRIGIDO')
    
    output_path = Path(output_file)
    
    print(f"\n💾 Salvando arquivo corrigido: {output_path}")
    
    # Salva com formatação preservada
    tree.write(output_path, encoding='utf-8', xml_declaration=True)
    
    print(f"\n{'='*80}")
    print(f"✅ CORREÇÃO CONCLUÍDA!")
    print(f"{'='*80}")
    print(f"📊 Total de rungs analisados: {total_rungs}")
    print(f"🔧 Total de rungs corrigidos: {rungs_fixed}")
    print(f"📁 Arquivo original (backup): {input_path.with_suffix('.smbp.backup')}")
    print(f"📁 Arquivo corrigido: {output_path}")
    print(f"{'='*80}\n")
    
    if rungs_fixed > 0:
        print("⚠️  IMPORTANTE:")
        print("   1. Abra o arquivo corrigido no SoMachine Basic")
        print("   2. Compile o projeto (F7)")
        print("   3. Faça download para o CLP")
        print("   4. Teste com o script test_modbus_mapped.py")
        print()
    
    return True

if __name__ == '__main__':
    print("\n" + "="*80)
    print("🔧 CORRETOR AUTOMÁTICO DO BUG DE MAPEAMENTO MODBUS - PROJETO UBEC")
    print("="*80 + "\n")
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = 'correto.smbp'
    
    output_file = None
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    success = fix_modbus_mapping(input_file, output_file)
    
    sys.exit(0 if success else 1)

