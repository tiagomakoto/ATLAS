"""
Fix double-encoded UTF-8 files in delta_chaos/.
Strategy: Use ftfy library if available, otherwise manual replacement with comprehensive mapping.
"""
import os
import glob
import shutil
import re

DC_DIR = r"C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos"
BACKUP_DIR = r"C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos_encoding_backup"

os.makedirs(BACKUP_DIR, exist_ok=True)

# Try ftfy first
try:
    import ftfy
    HAS_FTFY = True
except ImportError:
    HAS_FTFY = False
    print("ftfy not available, using manual replacement")

# Comprehensive manual replacement mapping
# These are UTF-8 bytes interpreted as cp1252
MANUAL_REPLACEMENTS = [
    # ══ box drawing double horizontal (U+2550)
    # UTF-8: E2 95 90 -> cp1252 interpretation: â•
    ("\u00e2\u2022\u0090", "\u2550"),
    ("\u00e2\u2022", "\u2550"),
    
    # ── box drawing single horizontal (U+2500)
    # UTF-8: E2 94 80 -> cp1252: â"€
    ("\u00e2\u20ac\u201d", "\u2500"),
    ("\u00e2\u201d", "\u2500"),
    
    # ç (U+00E7) - UTF-8: C3 A7 -> cp1252: Ã§
    ("\u00c3\u00a7", "\u00e7"),
    # é (U+00E9) - UTF-8: C3 A9 -> cp1252: Ã©
    ("\u00c3\u00a9", "\u00e9"),
    # ê (U+00EA) - UTF-8: C3 AA -> cp1252: Ãª
    ("\u00c3\u00aa", "\u00ea"),
    # ó (U+00F3) - UTF-8: C3 B3 -> cp1252: Ã³
    ("\u00c3\u00b3", "\u00f3"),
    # ô (U+00F4) - UTF-8: C3 B4 -> cp1252: Ã´
    ("\u00c3\u00b4", "\u00f4"),
    # ú (U+00FA) - UTF-8: C3 BA -> cp1252: Ãº
    ("\u00c3\u00ba", "\u00fa"),
    # í (U+00ED) - UTF-8: C3 AD -> cp1252: Ã­
    ("\u00c3\u00ad", "\u00ed"),
    # á (U+00E1) - UTF-8: C3 A1 -> cp1252: Ã¡
    ("\u00c3\u00a1", "\u00e1"),
    # ã (U+00E3) - UTF-8: C3 A3 -> cp1252: Ã£
    ("\u00c3\u00a3", "\u00e3"),
    # õ (U+00F5) - UTF-8: C3 B5 -> cp1252: Ãµ
    ("\u00c3\u00b5", "\u00f5"),
    
    # à (U+00E0) - UTF-8: C3 A0 -> cp1252: Ã 
    # This is the tricky one - Ã followed by space-like char
    ("\u00c3\u00a0", "\u00e0"),
    
    # È (U+00C8) - UTF-8: C3 88 -> cp1252: Ãˆ
    ("\u00c3\u0088", "\u00c8"),
    # É (U+00C9) - UTF-8: C3 89 -> cp1252: Ã‰
    ("\u00c3\u2030", "\u00c9"),
    # Í (U+00CD) - UTF-8: C3 8D -> cp1252: Ã
    ("\u00c3\u008d", "\u00cd"),
    # Ó (U+00D3) - UTF-8: C3 93 -> cp1252: Ã"
    ("\u00c3\u201c", "\u00d3"),
    # Ú (U+00DA) - UTF-8: C3 9A -> cp1252: Ãš
    ("\u00c3\u0161", "\u00da"),
    
    # — em dash (U+2014) - UTF-8: E2 80 94 -> cp1252: â€"
    ("\u00e2\u20ac\u201d", "\u2014"),
    # " left double quote (U+201C) - UTF-8: E2 80 9C -> cp1252: â€œ
    ("\u00e2\u20ac\u0153", "\u201c"),
    # " right double quote (U+201D) - UTF-8: E2 80 9D -> cp1252: â€"
    ("\u00e2\u20ac\u201d", "\u201d"),
    # ' left single quote (U+2018) - UTF-8: E2 80 98 -> cp1252: â€˜
    ("\u00e2\u20ac\u2018", "\u2018"),
    # ' right single quote (U+2019) - UTF-8: E2 80 99 -> cp1252: â€™
    ("\u00e2\u20ac\u2122", "\u2019"),
    
    # → right arrow (U+2192) - UTF-8: E2 86 92 -> cp1252: â†'
    ("\u00e2\u2020\u2019", "\u2192"),
    # ✓ check mark (U+2713) - UTF-8: E2 9C 93 -> cp1252: âœ"
    ("\u00e2\u0153\u201c", "\u2713"),
    # ✗ cross mark (U+2717) - UTF-8: E2 9C 97 -> cp1252: âœ"
    ("\u00e2\u0153\u2014", "\u2717"),
    # ⚠ warning (U+26A0) - UTF-8: E2 9A A0 -> cp1252: âš 
    ("\u00e2\u0161 ", "\u26a0"),
    
    # Non-breaking space artifact
    ("\u00c2\u00a0", "\u00a0"),
    ("\u00c2", ""),
]

py_files = sorted(glob.glob(os.path.join(DC_DIR, "*.py")))

fixed_count = 0
skip_count = 0
error_count = 0

for filepath in py_files:
    fname = os.path.basename(filepath)
    
    try:
        with open(filepath, 'rb') as f:
            raw_bytes = f.read()
    except Exception as e:
        print(f"[SKIP] {fname}: {e}")
        skip_count += 1
        continue
    
    # Decode as UTF-8
    try:
        text = raw_bytes.decode('utf-8')
    except UnicodeDecodeError:
        print(f"[SKIP] {fname}: not valid UTF-8")
        skip_count += 1
        continue
    
    # Check if file has mojibake
    mojibake_markers = [
        '\u00e2\u2022', '\u00c3\u00a9', '\u00c3\u00a7', '\u00c3\u00a3',
        '\u00c3\u00a1', '\u00c3\u00ad', '\u00c3\u00b3', '\u00c3\u00ba',
        '\u00c3\u00aa', '\u00c3\u00b4', '\u00c3\u00b5', '\u00c3\u00a0',
        '\u00e2\u20ac', '\u00e2\u2020', '\u00e2\u0153', '\u00e2\u0161',
    ]
    
    has_mojibake = any(m in text for m in mojibake_markers)
    
    if not has_mojibake:
        print(f"[OK]   {fname}")
        skip_count += 1
        continue
    
    if HAS_FTFY:
        fixed_text = ftfy.fix_text(text)
    else:
        # Manual replacement - order matters (longer patterns first)
        fixed_text = text
        for mojibake, correct in MANUAL_REPLACEMENTS:
            fixed_text = fixed_text.replace(mojibake, correct)
    
    if fixed_text == text:
        print(f"[SKIP] {fname}: no changes")
        skip_count += 1
        continue
    
    # Backup
    backup_path = os.path.join(BACKUP_DIR, fname)
    shutil.copy2(filepath, backup_path)
    
    # Write fixed
    with open(filepath, 'wb') as f:
        f.write(fixed_text.encode('utf-8'))
    
    # Verify
    with open(filepath, 'r', encoding='utf-8') as f:
        verify = f.read()
    still_broken = any(m in verify for m in mojibake_markers)
    if still_broken:
        print(f"[WARN] {fname}: partial fix")
        error_count += 1
    else:
        print(f"[FIXED] {fname}")
        fixed_count += 1

print(f"\n{'='*60}")
print(f"SUMMARY: {fixed_count} fixed, {error_count} partial, {skip_count} skipped/ok")
print(f"Backups: {BACKUP_DIR}")
