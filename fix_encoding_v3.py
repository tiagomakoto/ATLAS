"""
Fix encoding v3 - correção manual dos caracteres que o ftfy não resolveu.

Mapeamento de mojibake residual → caracteres corretos:
  âš  (U+00E2 U+0161 U+00A0) → ⚠ (U+26A0)
  â€" (U+00E2 U+20AC U+201D) → — (U+2014) em dash
  â•  (U+00E2 U+2022)        → ═ (U+2550) box drawing double horizontal
  â–ˆ (U+00E2 U+2013 U+02C6) → █ (U+2588) full block
  â›  (U+00E2 U+2039)        → ⛔ (U+26D4) no entry
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import glob
import shutil
import time

DC_DIR = r"C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos"
BACKUP_V2_DIR = r"C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos_encoding_backup_v2"

os.makedirs(BACKUP_V2_DIR, exist_ok=True)

# Mapeamento de mojibake → correto (ordem: padrões mais longos primeiro)
REPLACEMENTS = [
    # ⚠ warning sign: UTF-8 E2 9A A0 → cp1252 âš  → U+00E2 U+0161 U+00A0
    ('\u00e2\u0161\u00a0', '\u26a0'),
    
    # — em dash: UTF-8 E2 80 94 → cp1252 â€" → U+00E2 U+20AC U+201D
    ('\u00e2\u20ac\u201d', '\u2014'),
    
    # ═ box drawing double horizontal: UTF-8 E2 95 90 → cp1252 â• → U+00E2 U+2022 U+0090
    # Mas o que temos é â• (U+00E2 U+2022) sem o terceiro byte
    ('\u00e2\u2022', '\u2550'),
    
    # █ full block: UTF-8 E2 96 88 → cp1252 â–ˆ → U+00E2 U+2013 U+02C6
    ('\u00e2\u2013\u02c6', '\u2588'),
    
    # ⛔ no entry: UTF-8 E2 9B 94 → cp1252 â›" → U+00E2 U+2039 U+201D (aproximado)
    ('\u00e2\u2039', '\u26d4'),
    
    # ← left arrow: UTF-8 E2 86 90 → cp1252 â†' → pode estar correto ou não
    # Se estiver como ← já está correto (U+2190)
    
    # Δ Greek capital delta: UTF-8 CE 94 → cp1252 Î" → pode estar correto
    # Se estiver como Δ já está correto (U+0394)
]

def fix_file(filepath):
    """Aplica correções manuais de encoding."""
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    
    original = text
    for mojibake, correct in REPLACEMENTS:
        text = text.replace(mojibake, correct)
    
    if text != original:
        # Backup
        fname = os.path.basename(filepath)
        backup_path = os.path.join(BACKUP_V2_DIR, fname)
        shutil.copy2(filepath, backup_path)
        
        # Write fixed
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)
        return True
    return False

def main():
    py_files = sorted(glob.glob(os.path.join(DC_DIR, "*.py")))
    
    print(f"{'='*60}")
    print(f"FIX ENCODING V3 - Correção manual residual")
    print(f"{'='*60}\n")
    
    fixed_count = 0
    for i, filepath in enumerate(py_files):
        fname = os.path.basename(filepath)
        was_fixed = fix_file(filepath)
        if was_fixed:
            print(f"[{i+1}/{len(py_files)}] FIXED: {fname}")
            fixed_count += 1
        else:
            print(f"[{i+1}/{len(py_files)}] OK:     {fname}")
        
        if i < len(py_files) - 1:
            time.sleep(2)
    
    print(f"\n{'='*60}")
    print(f"Resumo: {fixed_count} corrigidos, {len(py_files) - fixed_count} já OK")
    print(f"Backups: {BACKUP_V2_DIR}")

if __name__ == "__main__":
    main()
