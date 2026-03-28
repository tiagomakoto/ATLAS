import os
from pathlib import Path

def print_tree(start_path, level=0, prefix=""):
    """Imprime a estrutura de diretórios em formato de árvore"""
    try:
        items = sorted(os.listdir(start_path))
    except PermissionError:
        return
    
    # Filtra pastas ocultas e __pycache__
    items = [i for i in items if not i.startswith('.') and i != '__pycache__']
    
    for i, item in enumerate(items):
        item_path = os.path.join(start_path, item)
        is_last = (i == len(items) - 1)
        
        # Símbolos para árvore
        connector = "└── " if is_last else "├── "
        print(f"{prefix}{connector}{item}")
        
        # Recursão para pastas
        if os.path.isdir(item_path):
            extension = "    " if is_last else "│   "
            print_tree(item_path, level + 1, prefix + extension)

def save_tree(start_path, output_file="atlas_structure.txt"):
    """Salva a estrutura em arquivo"""
    import sys
    from io import StringIO
    
    old_stdout = sys.stdout
    sys.stdout = buffer = StringIO()
    
    print(f"Estrutura do diretório: {start_path}\n")
    print_tree(start_path)
    
    sys.stdout = old_stdout
    tree_output = buffer.getvalue()
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(tree_output)
    
    print(f"\n✅ Estrutura salva em: {output_file}")
    return tree_output

if __name__ == "__main__":
    # Caminho base - ajuste se necessário
    base_path = r"C:\Users\tiago\OneDrive\Documentos\ATLAS"
    
    print(f"📁 Escaneando: {base_path}\n")
    
    if os.path.exists(base_path):
        print_tree(base_path)
        print()
        save_tree(base_path)
    else:
        print(f"❌ Diretório não encontrado: {base_path}")
        print("Edite a variável 'base_path' no script com o caminho correto.")