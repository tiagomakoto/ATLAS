from atlas_backend.main import app

print("=== Rotas registradas no FastAPI ===\n")
for route in app.routes:
    if hasattr(route, 'methods') and hasattr(route, 'path'):
        print(f"Path: {route.path} | Methods: {route.methods}")
    elif hasattr(route, 'path'):
        print(f"Path: {route.path} (sem métodos)")