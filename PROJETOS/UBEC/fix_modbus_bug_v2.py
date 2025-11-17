#!/usr/bin/env python3
"""
Script para corrigir o BUG de mapeamento Modbus - Versão 2
Manipula o XML como texto para manter formatação correta
"""

import re
import sys
from pathlib import Path

def backup_file(filepath):
    """Cria backup do arquivo original"""
    backup_path = filepath.with_suffix('.smbp.backup2')
    import shutil
    shutil.copy2(filepath, backup_path)
    print(f"✓ Backup criado: {backup_path}")
    return backup_path

def fix_instruction_block(content, start_pos):
    """
    Encontra e corrige um bloco de InstructionLines que contém [ %MWxxx := 1 ]
    Retorna (novo_conteudo, posicao_final, corrigido)
    """
    # Procura o padrão [ %MWxxx := 1 ] com contexto
    pattern = r'(<InstructionLineEntity>\s*<InstructionLine>\[\s*(%MW[56]\d{2})\s*:=\s*1\s*\]</InstructionLine>\s*<Comment\s*/>\s*</InstructionLineEntity>)'
    
    match = re.search(pattern, content[start_pos:])
    if not match:
        return content, len(content), False
    
    mw_register = match.group(2)
    original_instruction = match.group(1)
    
    # Encontra a variável de origem procurando para trás
    # Procura por <InstructionLine>LD ou ST %X</InstructionLine>
    before_content = content[:start_pos + match.start()]
    
    # Procura última instrução LD/ST antes desta
    ld_pattern = r'<InstructionLine>(LD|ST)\s+(%[IQM]\S+)</InstructionLine>'
    ld_matches = list(re.finditer(ld_pattern, before_content))
    
    if not ld_matches:
        return content, start_pos + match.end(), False
    
    last_ld = ld_matches[-1]
    source_var = last_ld.group(2)
    
    # Se for ST, procura o LD anterior
    if last_ld.group(1) == 'ST':
        # Pega a variável do LD anterior ao ST
        ld_matches_before_st = list(re.finditer(ld_pattern, before_content[:last_ld.start()]))
        if ld_matches_before_st:
            prev_instruction = ld_matches_before_st[-1]
            if prev_instruction.group(1) == 'LD':
                # Usa a variável física se começar com %
                if prev_instruction.group(2).startswith('%'):
                    source_var = prev_instruction.group(2)
    
    # Garante que source_var começa com %
    if not source_var.startswith('%'):
        # Tenta encontrar o símbolo correspondente procurando por <Symbol>
        symbol_pattern = rf'<Symbol>{re.escape(source_var)}</Symbol>'
        symbol_match = re.search(symbol_pattern, before_content[::-1])
        if not symbol_match:
            return content, start_pos + match.end(), False
        # Se não achar, mantém como está
    
    print(f"  🔧 Corrigindo: [ {mw_register} := 1 ]")
    print(f"     Variável origem: {source_var}")
    
    # Calcula indentação baseada na linha atual
    line_start = content.rfind('\n', 0, start_pos + match.start()) + 1
    indent = ' ' * (start_pos + match.start() - line_start)
    
    # Cria as novas linhas com formatação correta
    new_ld_line = f"{indent}<InstructionLineEntity>\n{indent}  <InstructionLine>LD    {source_var}</InstructionLine>\n{indent}  <Comment />\n{indent}</InstructionLineEntity>\n"
    
    new_ldn_line = f"{indent}<InstructionLineEntity>\n{indent}  <InstructionLine>LDN   {source_var}</InstructionLine>\n{indent}  <Comment />\n{indent}</InstructionLineEntity>\n"
    
    new_reset_line = f"{indent}<InstructionLineEntity>\n{indent}  <InstructionLine>[ {mw_register} := 0 ]</InstructionLine>\n{indent}  <Comment />\n{indent}</InstructionLineEntity>\n"
    
    # Monta o novo bloco: LD + original + LDN + RESET
    new_block = new_ld_line + original_instruction + "\n" + new_ldn_line + new_reset_line
    
    # Substitui no conteúdo
    new_content = (
        content[:start_pos + match.start()] +
        new_block +
        content[start_pos + match.end():]
    )
    
    print(f"     ✅ Adicionado: LD {source_var} / LDN {source_var} / [ {mw_register} := 0 ]")
    
    return new_content, start_pos + match.start() + len(new_block), True

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
    
    # Lê o arquivo como texto
    print(f"\n📖 Lendo arquivo: {input_file}")
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n🔍 Procurando e corrigindo bugs de mapeamento Modbus...\n")
    
    # Processa todas as ocorrências
    rungs_fixed = 0
    current_pos = 0
    
    while current_pos < len(content):
        new_content, next_pos, fixed = fix_instruction_block(content, current_pos)
        
        if fixed:
            rungs_fixed += 1
            content = new_content
            current_pos = next_pos
            print()
        else:
            # Avança para próxima possível ocorrência
            next_match = content.find('[ %MW', current_pos + 1)
            if next_match == -1:
                break
            current_pos = next_match
    
    # Salva o arquivo corrigido
    if output_file is None:
        output_file = input_path.with_stem(input_path.stem + '_CORRIGIDO')
    
    output_path = Path(output_file)
    
    print(f"💾 Salvando arquivo corrigido: {output_path}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n{'='*80}")
    print(f"✅ CORREÇÃO CONCLUÍDA!")
    print(f"{'='*80}")
    print(f"🔧 Total de rungs corrigidos: {rungs_fixed}")
    print(f"📁 Arquivo original (backup): {input_path.with_suffix('.smbp.backup2')}")
    print(f"📁 Arquivo corrigido: {output_path}")
    print(f"{'='*80}\n")
    
    if rungs_fixed > 0:
        print("⚠️  PRÓXIMOS PASSOS:")
        print("   1. Feche o SoMachine Basic se estiver aberto")
        print("   2. Abra o arquivo corrigido no SoMachine Basic")
        print("   3. Compile o projeto (F7)")
        print("   4. Faça download para o CLP")
        print()
    
    return True

if __name__ == '__main__':
    print("\n" + "="*80)
    print("🔧 CORRETOR AUTOMÁTICO DO BUG DE MAPEAMENTO MODBUS - VERSÃO 2")
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

