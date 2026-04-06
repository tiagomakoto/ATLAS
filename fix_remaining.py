"""
Fix remaining triple-encoded characters that ftfy missed.
"""
import os
import glob
import shutil

DC_DIR = r"C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos"

# These are triple-encoded patterns (UTF-8 -> cp1252 -> UTF-8 -> cp1252 -> UTF-8)
# The bytes we see are valid UTF-8 but represent mojibake
REPLACEMENTS = [
    # ÇÃ -> çã (triple-encoded ção)
    ("\u00c7\u00c3", "\u00e7\u00e3"),
    # Ã -> ã (triple-encoded ã)
    ("\u00c3 ", "\u00e3 "),  # Ã followed by space -> ã followed by space
    ("\u00c3n", "\u00e3n"),  # Ãn -> ãn
    ("\u00c3N", "\u00e3N"),  # ÃN -> ãN
    # Á -> á (triple-encoded á)
    ("\u00c1", "\u00e1"),
    # É -> é (triple-encoded é)
    ("\u00c9", "\u00e9"),
    # Í -> í (triple-encoded í)
    ("\u00cd", "\u00ed"),
    # Ó -> ó (triple-encoded ó)
    ("\u00d3", "\u00f3"),
    # Ú -> ú (triple-encoded ú)
    ("\u00da", "\u00fa"),
    # — em dash that survived
    ("\u2014", "\u2014"),  # already correct, skip
]

# Files with remaining issues
files_to_fix = [
    "book.py",
    "gate.py", 
    "orbit.py",
    "tape.py",
    "tune.py",
]

BACKUP_DIR = r"C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos_encoding_backup"

for fname in files_to_fix:
    filepath = os.path.join(DC_DIR, fname)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Apply replacements
    for mojibake, correct in REPLACEMENTS:
        content = content.replace(mojibake, correct)
    
    if content == original:
        print(f"[SKIP] {fname}: no changes")
        continue
    
    # Backup
    backup_path = os.path.join(BACKUP_DIR, fname)
    if not os.path.exists(backup_path):
        shutil.copy2(filepath, backup_path)
    
    # Write fixed
    with open(filepath, 'wb') as f:
        f.write(content.encode('utf-8'))
    
    print(f"[FIXED] {fname}")

# Verify all files
print("\nVerification:")
mojibake_markers = ['\u00c7\u00c3', '\u00c3 ', '\u00c3n', '\u00c1', '\u00c9', '\u00cd', '\u00d3', '\u00da']
for fname in sorted(os.listdir(DC_DIR)):
    if not fname.endswith('.py'):
        continue
    filepath = os.path.join(DC_DIR, fname)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    found = [m for m in mojibake_markers if m in content]
    if found:
        print(f"  [WARN] {fname}: {found}")
    else:
        print(f"  [CLEAN] {fname}")
