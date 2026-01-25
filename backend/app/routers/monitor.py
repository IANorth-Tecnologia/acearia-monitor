from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
import redis.asyncio as redis
import redis as redis_sync
import asyncio
import os
import time

router = APIRouter()
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"WS Conectado. Total: {len(self.active_connections)}")
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections: self.active_connections.remove(websocket)
        print(f"WS Desconectado. Total: {len(self.active_connections)}")
    async def broadcast(self, message: str):
        for connection in self.active_connections[:]:
            try: await connection.send_text(message)
            except: self.disconnect(connection)

manager = ConnectionManager()

async def redis_listener():
    print(f"Iniciando Listener Redis no host: {REDIS_HOST}")
    while True:
        try:
            r = redis.from_url(f"redis://{REDIS_HOST}", decode_responses=True)
            pubsub = r.pubsub()
            await pubsub.subscribe("safety_alerts")
            print("Inscrito no canal 'safety_alerts' com sucesso!")
            
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message["type"] == "message":
                    await manager.broadcast(message["data"])
                await asyncio.sleep(0.01) 

        except Exception as e:
            print(f"Erro na conexão com Redis: {e}. Tentando em 3s...")
            await asyncio.sleep(3)

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True: await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.get("/video_feed")
def video_feed():
    r_sync = redis_sync.Redis(host=REDIS_HOST, decode_responses=False)
    def generate():
        while True:
            try:
                frame = r_sync.get("live_frame")
                if frame:
                    yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                    time.sleep(0.04)
                else: time.sleep(0.1)
            except: time.sleep(1)
    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace;boundary=frame")
