from fastapi import WebSocket
from typing import List

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # print(f"[WS-MANAGER] Conectado — total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            # print(f"[WS-MANAGER] Desconectado — total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        event_type = message.get("type", "unknown")
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                # print(f"[WS-MANAGER] Falha ao enviar {event_type}: {e}")
                dead.append(connection)
        for d in dead:
            self.disconnect(d)
        # if self.active_connections:
        #     print(f"[WS-MANAGER] Broadcast {event_type} → {len(self.active_connections)} conexões")
        # else:
        #     print(f"[WS-MANAGER] ⚠️ Broadcast {event_type} — NENHUMA conexão ativa!")

manager = ConnectionManager()
