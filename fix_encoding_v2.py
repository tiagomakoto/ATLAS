"""
Fix encoding dos arquivos delta_chaos/ — versão segura com rate limiting.

Este script:
1. Restaura cada arquivo do backup (mojibake consistente)
2. Aplica ftfy para corrigir o encoding
3. Verifica o resultado
4. Sleep entre arquivos para evitar rate limiting no Alibaba Cloud

Uso: python fix_encoding_v2.py
"""
import os
import glob
import shutil
import time
import sys

# Reconfigurar stdout para UTF-8
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

import ftfy

DC_DIR = r"C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos"
BACKUP_DIR = r"C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos_encoding_backup"
VERIFY_BACKUP_DIR = r"C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos_encoding_backup_v2"

# Sleep entre arquivos (segundos) — ajustável conforme necessidade
SLEEP_BETWEEN_FILES = 5  # 5 segundos entre cada arquivo

os.makedirs(VERIFY_BACKUP_DIR, exist_ok=True)

# Padrões de mojibake para verificação
MOJIBAKE_MARKERS = [
    'Ã©', 'Ã§', 'Ã£o', 'Ã£', 'Ã¡', 'Ã­', 'Ã³', 'Ãº',
    'Ãª', 'Ã´', 'Ãµ', 'Ã"', 'Ã‰', 'Ãš',
    'â€"', 'â€œ', 'â€', 'â€˜', 'â€™',
    'â•', 'â"', 'â†', 'âœ', 'âš',
    'Ã',  # último para evitar falsos positivos parciais
]

def has_mojibake(text):
    """Verifica se o texto contém mojibake."""
    return any(m in text for m in MOJIBAKE_MARKERS)

def fix_file(fname):
    """Restaura do backup, aplica ftfy e verifica."""
    backup_path = os.path.join(BACKUP_DIR, fname)
    current_path = os.path.join(DC_DIR, fname)
    verify_path = os.path.join(VERIFY_BACKUP_DIR, fname)
    
    if not os.path.exists(backup_path):
        return 'SKIP', 'backup não encontrado'
    
    # Ler backup
    try:
        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_text = f.read()
    except Exception as e:
        return 'ERRO', f'leitura backup: {e}'
    
    if not has_mojibake(backup_text):
        return 'OK', 'backup já está limpo'
    
    # Backup de segurança do estado atual
    if os.path.exists(current_path):
        shutil.copy2(current_path, verify_path)
    
    # Aplicar ftfy
    fixed_text = ftfy.fix_text(backup_text)
    
    # Verificar se ainda há mojibake
    still_broken = has_mojibake(fixed_text)
    
    if still_broken:
        # Tentar com opções adicionais
        fixed_text = ftfy.fix_text(backup_text, normalization='NFC')
        still_broken = has_mojibake(fixed_text)
    
    # Escrever arquivo corrigido
    try:
        with open(current_path, 'w', encoding='utf-8') as f:
            f.write(fixed_text)
    except Exception as e:
        return 'ERRO', f'escrita: {e}'
    
    # Verificação final
    with open(current_path, 'r', encoding='utf-8') as f:
        verify_text = f.read()
    
    final_broken = has_mojibake(verify_text)
    
    if final_broken:
        return 'PARCIAL', 'algum mojibake persistiu'
    else:
        return 'FIXED', 'corrigido com sucesso'

def main():
    py_files = sorted(glob.glob(os.path.join(DC_DIR, "*.py")))
    fnames = [os.path.basename(f) for f in py_files]
    
    # Adicionar arquivos que existem no backup mas não no DC_DIR
    backup_files = sorted(glob.glob(os.path.join(BACKUP_DIR, "*.py")))
    for bf in backup_files:
        fname = os.path.basename(bf)
        if fname not in fnames:
            fnames.append(fname)
    
    print(f"{'='*70}")
    print(f"FIX ENCODING V2 — {len(fnames)} arquivos para processar")
    print(f"Sleep entre arquivos: {SLEEP_BETWEEN_FILES}s")
    print(f"{'='*70}\n")
    
    results = []
    for i, fname in enumerate(fnames):
        status, msg = fix_file(fname)
        results.append((fname, status, msg))
        print(f"[{i+1}/{len(fnames)}] {fname}: {status} — {msg}")
        
        # Sleep entre arquivos (exceto no último)
        if i < len(fnames) - 1:
            print(f"  ⏳ Aguardando {SLEEP_BETWEEN_FILES}s...")
            time.sleep(SLEEP_BETWEEN_FILES)
    
    # Resumo
    print(f"\n{'='*70}")
    print("RESUMO")
    print(f"{'='*70}")
    
    counts = {}
    for fname, status, msg in results:
        counts[status] = counts.get(status, 0) + 1
        print(f"  {status:8s} — {fname}: {msg}")
    
    print(f"\nTotais:")
    for status, count in sorted(counts.items()):
        print(f"  {status}: {count}")
    
    print(f"\nBackups de segurança: {VERIFY_BACKUP_DIR}")
    print(f"Backups originais: {BACKUP_DIR}")

if __name__ == "__main__":
    main()
