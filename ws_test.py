# ws_test.py
# Cliente de teste WebSocket para ATLAS Backend — logs em tempo real
# Conecta em /ws/logs e escuta mensagens broadcast de todos os módulos

import asyncio
import websockets
import sys
from datetime import datetime

async def test():
    # ⚠️ ROTA: Deve bater com @app.websocket() em main.py
    # Atualmente: /ws/logs (NÃO /delta-chaos/ws/logs)
    uri = "ws://localhost:8000/ws/logs"
    
    print(f"=" * 60)
    print(f"  ATLAS WebSocket Test Client")
    print(f"  URI: {uri}")
    print(f"  Timeout: 120s (suficiente para TUNE/ORBIT)")
    print(f"=" * 60)
    print(f"\n-> Conectando a {uri}...")
    
    try:
        async with websockets.connect(uri, ping_interval=None, ping_timeout=None) as ws:
            print(f"✅ OK Conectado! Aguardando logs...")
            print(f"   (Ctrl+C para sair)\n")
            
            msg_count = 0
            while True:
                try:
                    # Timeout longo para processos pesados (TUNE ~60-90s)
                    msg = await asyncio.wait_for(ws.recv(), timeout=1200.0)
                    msg_count += 1
                    
                    # Timestamp local para cada mensagem
                    ts = datetime.now().strftime("%H:%M:%S")
                    
                    # Tenta parsear JSON para formatar bonito
                    try:
                        import json
                        data = json.loads(msg)
                        msg_type = data.get("type", "unknown")
                        level = data.get("level", "info")
                        message = data.get("message", str(data))
                        
                        # Cores por nível
                        level_colors = {
                            "debug": "\033[90m",    # cinza
                            "info": "\033[92m",     # verde
                            "warning": "\033[93m",  # amarelo
                            "error": "\033[91m",    # vermelho
                        }
                        color = level_colors.get(level, "\033[0m")
                        reset = "\033[0m"
                        
                        print(f"[{ts}] {color}[{level.upper()}]{reset} {message}")
                        
                    except json.JSONDecodeError:
                        print(f"[{ts}] [RAW] {msg}")
                        
                except asyncio.TimeoutError:
                    print(f"\n⚠️  Timeout de 1200s sem mensagens — conexão ainda ativa")
                    print(f"   Aguardando próxima mensagem... (Ctrl+C para sair)\n")
                    
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"\n❌ ERRO: Conexão fechada pelo servidor — {e}")
        sys.exit(1)
    except websockets.exceptions.InvalidStatus as e:
        print(f"\n❌ ERRO: HTTP {e.status_code} no handshake")
        print(f"   Verifique se a rota WebSocket está correta em main.py")
        print(f"   Esperado: @app.websocket('/ws/logs')")
        sys.exit(1)
    except ConnectionRefusedError:
        print(f"\n❌ ERRO: Servidor não responde em localhost:8000")
        print(f"   Inicie: python -m uvicorn atlas_backend.main:app --reload")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERRO: {type(e).__name__}: {e}")
        sys.exit(1)
    
    print(f"\n" + "=" * 60)
    print(f"  Teste concluído — {msg_count} mensagens recebidas")
    print(f"=" * 60)

if __name__ == "__main__":
    try:
        asyncio.run(test())
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Interrompido pelo usuário")
        sys.exit(0)