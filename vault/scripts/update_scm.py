#!/usr/bin/env python3
"""
update_scm.py — Atualiza arquivos SCM do vault após modificações de código.

Uso:
    python update_scm.py <arquivo1> <arquivo2> ...

Cada argumento é um caminho de arquivo modificado no commit.
O script identifica o sistema correspondente, atualiza/cria o .md apropriado.

COVERAGE_MAP: mapeia padrões de caminho para módulos conceituais existentes.
Se um arquivo modificado bate com um padrão, o módulo conceitual é atualizado
em vez de criar um novo .md por arquivo.
"""

import sys
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
    "atlas_backend": "atlas",
    "atlas_ui": "atlas",
    "advantage": "advantage",
}

# Mapeia padrões de caminho para módulo conceitual existente no vault.
# Chave: substring do caminho do arquivo modificado (lowercase)
# Valor: nome do arquivo .md conceitual (sem extensão)
# Se o arquivo bate com um padrão, atualiza o módulo conceitual
# em vez de criar um .md granular por arquivo.
COVERAGE_MAP = {
    # Delta Chaos
    "delta_chaos/tape.py":   "TAPE",
    "delta_chaos/orbit.py":  "ORBIT",
    "delta_chaos/fire.py":   "FIRE",
    "delta_chaos/book.py":   "BOOK",
    "delta_chaos/edge.py":   "EDGE",
    "delta_chaos/gate.py":   "GATE",
    "delta_chaos/gate_eod":  "GATE",
    "delta_chaos/tune.py":   "TUNE",

    # Advantage — Data Layer
    "advantage/src/data_layer/db/":          "DATA_LAYER",
    "advantage/src/data_layer/__init__":      "DATA_LAYER",
    "advantage/src/data_layer/collectors/":  "COLLECTORS",
    "advantage/src/data_layer/scheduler":    "SCHEDULER",
    "advantage/src/data_layer/utils":        "COLLECTORS",

    # Atlas backend
    "atlas_backend/core/dc_runner":    "dc_runner",
    "atlas_backend/core/event_bus":    "event_bus",
    "atlas_backend/core/config":       "config_manager",
    "atlas_backend/api/routes/":       "api_routes",
    "atlas_backend/api/websocket/":    "websocket",
}

# Extensões ignoradas — não geram .md
IGNORED_EXTENSIONS = {
    ".json", ".md", ".txt", ".lock", ".css",
    ".html", ".zip", ".log", ".done", ".jsonl",
    ".parquet", ".db", ".xlsx", ".zip",
}

# Arquivos e pastas ignorados por nome
IGNORED_PATTERNS = {
    "__init__", ".gitignore", ".gitattributes",
    "requirements", "package", "vite.config",
    "ADVANTAGE_DataLayer", "SPEC_", "README",
    "test_", "conftest", "pytest", "/tests/",
}


def detect_system(file_path: str) -> Optional[str]:
    """Detecta o sistema com base no caminho do arquivo."""
    file_path_lower = file_path.lower().replace("\\", "/")
    for key, system in SYSTEMS_MAP.items():
        if key in file_path_lower:
            return system
    return None


def should_ignore(file_path: str) -> bool:
    """Retorna True se o arquivo deve ser ignorado pelo SCM."""
    path = Path(file_path)
    normalized = file_path.lower().replace("\\", "/")

    # Pastas ignoradas no caminho
    ignored_dirs = {"/tests/", "/test/", "/__pycache__/", "/.git/", "/node_modules/"}
    for d in ignored_dirs:
        if d in normalized:
            return True

    # Extensão ignorada
    if path.suffix.lower() in IGNORED_EXTENSIONS:
        return True

    # Nome ignorado
    for pattern in IGNORED_PATTERNS:
        if pattern.lower() in path.name.lower():
            return True

    return True if path.name.startswith("test_") else False


def find_coverage(file_path: str, system: str) -> Optional[str]:
    """
    Retorna o nome do módulo conceitual que cobre este arquivo,
    ou None se não houver cobertura mapeada.
    """
    normalized = file_path.lower().replace("\\", "/")
    for pattern, module_name in COVERAGE_MAP.items():
        if pattern.lower() in normalized:
            # Verifica se o .md conceitual existe no vault
            md_path = SYSTEMS_DIR / system / "modules" / f"{module_name}.md"
            if md_path.exists():
                return module_name
    return None


def get_module_md_path(system: str, file_path: str) -> Optional[Path]:
    """Retorna o caminho do .md correspondente — por nome de stem."""
    if not system:
        return None
    base_name = Path(file_path).stem
    module_dir = SYSTEMS_DIR / system / "modules"
    if not module_dir.exists():
        return None
    for md_file in module_dir.glob("*.md"):
        if md_file.stem.lower() == base_name.lower():
            return md_file
    return None


def generate_uid(system: str, existing_uids: list) -> str:
    """Gera um uid sequencial para um novo módulo."""
    domain = system.split("_")[0] if system else "sys"
    counter = 1
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
    """Incrementa a versão patch."""
    match = re.match(r"(\d+)\.(\d+)\.?(\d*)", version_str.strip())
    if match:
        major, minor, patch = match.groups()
        patch = int(patch) if patch else 0
        return f"{major}.{minor}.{patch + 1}"
    return "1.0.1"


def needs_board_review(content: str) -> list:
    """Retorna lista de campos que precisam de revisão."""
    review_needed = []
    for field in ["intent", "constraints", "role", "function"]:
        pattern = rf"^{field}[:\s].*\[BOARD_REVIEW_REQUIRED\]"
        if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
            review_needed.append(field)
    return review_needed


def update_module_md(md_path: Path, code_file: str) -> list:
    """Atualiza um .md existente — incrementa versão e adiciona nota."""
    content = md_path.read_text(encoding="utf-8")
    new_content = content

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
    notes_entry = f"  - {today}: código modificado — {Path(code_file).name}"

    if re.search(r"^notes:", new_content, re.MULTILINE):
        new_content = re.sub(
            r"^(notes:)",
            f"\\1\n{notes_entry}",
            new_content,
            flags=re.MULTILINE
        )
    else:
        new_content += f"\n\nnotes:\n{notes_entry}"

    review_fields = needs_board_review(new_content)
    md_path.write_text(new_content, encoding="utf-8")
    return [md_path.name, new_version, review_fields]


def create_module_md(system: str, code_file: str) -> tuple:
    """Cria um novo .md a partir do template."""
    module_dir = SYSTEMS_DIR / system / "modules"
    module_dir.mkdir(parents=True, exist_ok=True)

    template_content = MODULE_TEMPLATE.read_text(encoding="utf-8")
    existing_uids = get_existing_uids(system)
    uid = generate_uid(system, existing_uids)
    base_name = Path(code_file).stem

    new_content = re.sub(r"^uid:\s*mod-.+$", f"uid: {uid}", template_content, flags=re.MULTILINE)
    new_content = re.sub(r"^function:.*$", "function: [BOARD_REVIEW_REQUIRED]", new_content, flags=re.MULTILINE)
    new_content = re.sub(r"^file:.*$", f"file: {code_file}", new_content, flags=re.MULTILINE)
    new_content = re.sub(r"^role:.*$", "role: [BOARD_REVIEW_REQUIRED]", new_content, flags=re.MULTILINE)
    new_content = re.sub(r"^intent:.*$", "intent: [BOARD_REVIEW_REQUIRED]", new_content, flags=re.MULTILINE)
    new_content = re.sub(r"^constraints:.*$", "constraints: [BOARD_REVIEW_REQUIRED]", new_content, flags=re.MULTILINE)

    today = datetime.now().strftime("%Y-%m-%d")
    notes_entry = f"  - {today} — módulo criado automaticamente a partir de {code_file}"
    new_content = re.sub(r"^notes:.*$", f"notes:\n{notes_entry}", new_content, flags=re.MULTILINE)

    md_path = module_dir / f"{base_name}.md"
    md_path.write_text(new_content, encoding="utf-8")
    return (md_path.name, uid, ["intent", "constraints", "role", "function"])


def update_scm(changed_files: list) -> dict:
    """Processa lista de arquivos modificados e atualiza o SCM."""
    results = {"updated": [], "created": [], "skipped": [], "review_required": []}

    for code_file in changed_files:
        # Ignora extensões e arquivos não relevantes
        if should_ignore(code_file):
            results["skipped"].append(code_file)
            continue

        system = detect_system(code_file)
        if not system:
            results["skipped"].append(code_file)
            continue

        # Verifica cobertura por módulo conceitual
        covered_by = find_coverage(code_file, system)
        if covered_by:
            md_path = SYSTEMS_DIR / system / "modules" / f"{covered_by}.md"
            updated_info = update_module_md(md_path, code_file)
            results["updated"].append({
                "file": updated_info[0],
                "version": updated_info[1],
                "review_fields": updated_info[2],
                "source": code_file,
            })
            if updated_info[2]:
                results["review_required"].append({
                    "file": updated_info[0],
                    "fields": updated_info[2],
                })
            continue

        # Sem cobertura — verifica se existe .md por stem
        md_path = get_module_md_path(system, code_file)
        if md_path and md_path.exists():
            updated_info = update_module_md(md_path, code_file)
            results["updated"].append({
                "file": updated_info[0],
                "version": updated_info[1],
                "review_fields": updated_info[2],
                "source": code_file,
            })
            if updated_info[2]:
                results["review_required"].append({
                    "file": updated_info[0],
                    "fields": updated_info[2],
                })
        else:
            # Cria novo .md granular apenas para arquivos sem cobertura
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
    print(f"Processando {len(changed_files)} arquivo(s)...\n")

    results = update_scm(changed_files)

    if results["updated"]:
        print("Arquivos SCM atualizados:")
        for item in results["updated"]:
            print(f" - {item['file']} (v{item['version']}) --> {Path(item['source']).name}")
        print()

    if results["created"]:
        print("Arquivos SCM criados:")
        for item in results["created"]:
            print(f"  - {item['file']} (uid: {item['uid']})")
        print()

    if results["skipped"]:
        print(f"Ignorados: {len(results['skipped'])} arquivo(s)")
        print()

    if results["review_required"]:
        print("Campos pendentes de revisão do board:")
        for item in results["review_required"]:
            print(f"  - {item['file']}: {', '.join(item['fields'])}")
    else:
        print("Nenhum campo requer revisão do board.")

    print("\nScript concluído. Commit dos arquivos do vault feito pelo OpenCode.")


if __name__ == "__main__":
    main()
