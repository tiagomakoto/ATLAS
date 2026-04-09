#!/usr/bin/env python3
"""
update_scm.py — Atualiza arquivos SCM do vault após modificações de código.

Uso:
    python update_scm.py <arquivo1> <arquivo2> ...

Cada argumento é um caminho de arquivo modificado no commit.
O script identifica o sistema correspondente, atualiza/cria o .md apropriado.
"""

import sys
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

VAULT_ROOT = Path(__file__).parent.parent
SYSTEMS_DIR = VAULT_ROOT / "SYSTEMS"
TEMPLATES_DIR = VAULT_ROOT / "TEMPLATES"
MODULE_TEMPLATE = TEMPLATES_DIR / "module_template.md"

SYSTEMS_MAP = {
    "delta_chaos": "delta_chaos",
    "atlas": "atlas",
    "advantage": "advantage",
}

def detect_system(file_path: str) -> Optional[str]:
    """Detecta o sistema对应的 based no caminho do arquivo."""
    file_path_lower = file_path.lower()
    
    for key in SYSTEMS_MAP:
        if key in file_path_lower:
            return key
    
    return None

def get_module_md_path(system: str, file_path: str) -> Optional[Path]:
    """Retorna o caminho do arquivo .md correspondente no vault."""
    if not system:
        return None
    
    base_name = Path(file_path).stem
    module_dir = SYSTEMS_DIR / system / "modules"
    
    if not module_dir.exists():
        return None
    
    for md_file in module_dir.glob("*.md"):
        if md_file.stem == base_name:
            return md_file
    
    return None

def generate_uid(system: str, existing_uids: list) -> str:
    """Gera um uid sequencial para um novo módulo."""
    counter = 1
    domain = system.split("_")[0] if system else "sys"
    
    while True:
        uid = f"mod-{domain}-{counter:03d}"
        if uid not in existing_uids:
            return uid
        counter += 1

def get_existing_uids(system: str) -> list:
    """Lista todos os UIDs existentes para um sistema."""
    module_dir = SYSTEMS_DIR / system / "modules"
    uids = []
    
    if not module_dir.exists():
        return uids
    
    for md_file in module_dir.glob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        match = re.search(r"^uid:\s*(.+)$", content, re.MULTILINE)
        if match:
            uids.append(match.group(1).strip())
    
    return uids

def increment_version(version_str: str) -> str:
    """Incrementa a versão (patch level)."""
    match = re.match(r"(\d+)\.(\d+)\.(\d+)", version_str)
    if match:
        major, minor, patch = match.groups()
        return f"{major}.{minor}.{int(patch) + 1}"
    return "1.0.1"

def needs_board_review(content: str) -> bool:
    """Verifica se campos requerem revisão do board."""
    review_needed = []
    
    intent_match = re.search(r"^intent:\s*-\s*(.+)$", content, re.MULTILINE)
    if intent_match and "[BOARD_REVIEW_REQUIRED]" in intent_match.group(1):
        review_needed.append("intent")
    
    constraints_match = re.search(r"^constraints:\s*-\s*(.+)$", content, re.MULTILINE)
    if constraints_match and "[BOARD_REVIEW_REQUIRED]" in constraints_match.group(1):
        review_needed.append("constraints")
    
    return review_needed

def update_module_md(md_path: Path, code_file: str) -> list:
    """Atualiza um arquivo .md existente."""
    content = md_path.read_text(encoding="utf-8")
    new_content = content
    review_fields = []
    
    version_match = re.search(r"^version:\s*(.+)$", content, re.MULTILINE)
    current_version = version_match.group(1).strip() if version_match else "1.0"
    new_version = increment_version(current_version)
    new_content = re.sub(
        r"^version:\s*.+$",
        f"version: {new_version}",
        new_content,
        flags=re.MULTILINE
    )
    
    today = datetime.now().strftime("%Y-%m-%d")
    notes_entry = f"- {today}: código modificado — {Path(code_file).name}"
    
    if re.search(r"^notes:", new_content, re.MULTILINE):
        new_content = re.sub(
            r"^(notes:)",
            f"\g<1>\n  {notes_entry}",
            new_content,
            flags=re.MULTILINE
        )
    else:
        new_content += f"\n\nnotes:\n  {notes_entry}"
    
    review_fields = needs_board_review(new_content)
    
    md_path.write_text(new_content, encoding="utf-8")
    
    return [md_path.name, new_version, review_fields]

def create_module_md(system: str, code_file: str) -> tuple:
    """Cria um novo arquivo .md a partir do template."""
    module_dir = SYSTEMS_DIR / system / "modules"
    module_dir.mkdir(parents=True, exist_ok=True)
    
    template_content = MODULE_TEMPLATE.read_text(encoding="utf-8")
    
    existing_uids = get_existing_uids(system)
    uid = generate_uid(system, existing_uids)
    
    base_name = Path(code_file).stem
    
    new_content = template_content.replace("<domain>-<number>", uid.replace("mod-", ""))
    new_content = re.sub(r"^uid:\s*mod-.+$", f"uid: {uid}", new_content, flags=re.MULTILINE)
    new_content = re.sub(r"^function:", f"function: [BOARD_REVIEW_REQUIRED]", new_content, flags=re.MULTILINE)
    new_content = re.sub(r"^file:", f"file: {code_file}", new_content, flags=re.MULTILINE)
    new_content = re.sub(r"^role:", f"role: [BOARD_REVIEW_REQUIRED]", new_content, flags=re.MULTILINE)
    new_content = re.sub(r"^intent:\s*-\s*\[BOARD_REVIEW_REQUIRED\]", "intent: [BOARD_REVIEW_REQUIRED]", new_content, flags=re.MULTILINE)
    new_content = re.sub(r"^constraints:\s*-\s*<regras", "constraints: [BOARD_REVIEW_REQUIRED] — thresholds literais", new_content, flags=re.MULTILINE)
    
    notes_entry = f"- {datetime.now().strftime('%Y-%m-%d')} — módulo criado automaticamente a partir de {code_file}"
    new_content = re.sub(
        r"^notes:\s*-\s*<edge",
        f"notes:\n  {notes_entry}",
        new_content,
        flags=re.MULTILINE
    )
    
    md_path = module_dir / f"{base_name}.md"
    md_path.write_text(new_content, encoding="utf-8")
    
    return (md_path.name, uid, ["intent", "constraints", "role", "function"])

def update_scm(changed_files: list) -> dict:
    """Processa lista de arquivos modificados e atualiza o SCM."""
    results = {
        "updated": [],
        "created": [],
        "review_required": [],
    }
    
    for code_file in changed_files:
        system = detect_system(code_file)
        
        if not system:
            continue
        
        md_path = get_module_md_path(system, code_file)
        
        if md_path and md_path.exists():
            updated_info = update_module_md(md_path, code_file)
            results["updated"].append({
                "file": updated_info[0],
                "version": updated_info[1],
                "review_fields": updated_info[2],
            })
            if updated_info[2]:
                results["review_required"].append({
                    "file": updated_info[0],
                    "fields": updated_info[2],
                })
        else:
            created_info = create_module_md(system, code_file)
            results["created"].append({
                "file": created_info[0],
                "uid": created_info[1],
                "review_fields": created_info[2],
            })
            results["review_required"].append({
                "file": created_info[0],
                "fields": created_info[2],
            })
    
    return results

def main():
    if len(sys.argv) < 2:
        print("Uso: python update_scm.py <arquivo1> <arquivo2> ...")
        sys.exit(1)
    
    changed_files = sys.argv[1:]
    
    print(f"Processando {len(changed_files)} arquivo(s) modificado(s)...")
    print()
    
    results = update_scm(changed_files)
    
    if results["updated"]:
        print("Arquivos SCM atualizados:")
        for item in results["updated"]:
            print(f"  - {item['file']} (v{item['version']})")
        print()
    
    if results["created"]:
        print("Arquivos SCM criados:")
        for item in results["created"]:
            print(f"  - {item['file']} (uid: {item['uid']})")
        print()
    
    if results["review_required"]:
        print("Campos que requerem revisão do board:")
        for item in results["review_required"]:
            print(f"  - {item['file']}: {', '.join(item['review_fields'])}")
    else:
        print("Nenhum campo requer revisão do board.")
    
    print()
    print("Script executado. O commit dos arquivos do vault deve ser feito separadamente.")

if __name__ == "__main__":
    main()