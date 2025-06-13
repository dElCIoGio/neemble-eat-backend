from functools import lru_cache
from typing import Dict, List
from fastapi import WebSocket
from threading import Lock

from starlette.websockets import WebSocketState


class WebsocketConnectionManager:
    _instance = None
    _lock: Lock = Lock()

    def __new__(cls):
        with cls._lock:
            if not cls._instance:
                cls._instance = super(WebsocketConnectionManager, cls).__new__(cls)
                cls._instance.active_connections: Dict[str, List[WebSocket]] = {}
            return cls._instance

    async def connect(self, websocket: WebSocket, key: str):
        await websocket.accept()
        if key not in self.active_connections:
            self.active_connections[key] = []
        self.active_connections[key].append(websocket)

    async def disconnect(self, websocket: WebSocket, key: str):
        if key in self.active_connections:
            self.active_connections[key].remove(websocket)
            if not websocket.client_state == WebSocketState.DISCONNECTED:
                await websocket.close()

    async def broadcast(self, message: str, key: str):
        with self._lock:
            if key in self.active_connections:
                for connection in self.active_connections[key][:]:
                    if connection.client_state == WebSocketState.CONNECTED:
                        try:
                            await connection.send_text(message)
                        except Exception as e:
                            print(f"Failed to send message to {connection}: {e}")
                            self.active_connections[key].remove(connection)
                    else:
                        self.active_connections[key].remove(connection)

@lru_cache
def get_websocket_manger():
    manager = WebsocketConnectionManager()
    return manager
