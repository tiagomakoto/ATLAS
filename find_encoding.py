import os
import glob

DC_DIR = r"C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos"

MOJIBAKE_PATTERNS = [
    'â•', 'â"', 'Ã©', 'Ã§', 'Ã£o', 'Ã£', 'Ã¡', 'Ã­', 'Ã³', 'Ãº',
    'Ã"', 'Ãª', 'Ã´', 'â€"', 'â€"', 'â€"', 'â€"', 'â€"', 'â†"',
    'âœ"', 'âœ"', 'âš ', 'Ã',
]

json_files = sorted(glob.glob(os.path.join(DC_DIR, "*.py")))

output_lines = []

for filepath in json_files:
    fname = os.path.basename(filepath)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        continue

    lines = content.split('\n')
    found_issues = []

    for line_num, line in enumerate(lines, 1):
        for pattern in MOJIBAKE_PATTERNS:
            if pattern in line:
                # Clean the snippet to avoid BOM and other issues
                clean_snippet = line.strip()[:120].encode('ascii', 'replace').decode('ascii')
                found_issues.append((line_num, pattern.encode('ascii', 'replace').decode('ascii'), clean_snippet))
                break

    if found_issues:
        output_lines.append(f"\n{'='*80}")
        output_lines.append(f"FILE: {fname} ({len(found_issues)} lines with encoding issues)")
        output_lines.append(f"{'='*80}")
        for line_num, pattern, snippet in found_issues:
            output_lines.append(f"  L{line_num:4d} [{pattern}] {snippet}")

with open(r"C:\Users\tiago\OneDrive\Documentos\ATLAS\encoding_report.txt", 'w', encoding='utf-8') as f:
    f.write('\n'.join(output_lines))

print(f"Report written to encoding_report.txt")
print(f"Total files with issues: {sum(1 for fp in json_files if os.path.basename(fp) in open(r'C:\Users\tiago\OneDrive\Documentos\ATLAS\encoding_report.txt', encoding='utf-8').read())}")
