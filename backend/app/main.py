import cv2
import os
import time
import threading
import queue
import requests
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from object_segmentation import ObjectSegmentation
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

RTSP_URL = os.getenv("RTSP_URL", "0") 
MODEL_PATH = "models/pan28.pt"
ARDUINO_URL = "http://192.168.1.000" 

global_frame = None
global_status_data = {
    "status": "INICIANDO",
    "perigo": False
}

class ArduinoStatusResponse(BaseModel):
    status: str
    perigo: bool
    timestamp: float 

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active_connections.append(ws)
    def disconnect(self, ws: WebSocket):
        if ws in self.active_connections: self.active_connections.remove(ws)
    async def broadcast(self, data: dict):
        for connection in self.active_connections[:]:
            try: await connection.send_json(data)
            except: self.disconnect(connection)

manager = ConnectionManager()

class VideoCaptureThread:
    def __init__(self, src):
        self.src = int(src) if src.isdigit() else src
        self.cap = cv2.VideoCapture(self.src)
        self.q = queue.Queue(maxsize=1) 
        self.stopped = False
        if self.cap.isOpened():
            threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self):
        while not self.stopped:
            ret, frame = self.cap.read()
            if not ret: break
            if not self.q.empty():
                try: self.q.get_nowait()
                except queue.Empty: pass
            self.q.put(frame)

    def read(self):
        try: return self.q.get(timeout=2.0)
        except queue.Empty: return None 
    def release(self):
        self.stopped = True
        self.cap.release()

def ai_loop():
    global global_frame, global_status_data
    
    print("[IA] Carregando Modelo...")
    try:
        segmentation_engine = ObjectSegmentation(MODEL_PATH)
    except Exception as e:
        print(f"[IA] Erro Fatal no Modelo: {e}")
        return

    last_arduino_status = None

    while True:
        cam = VideoCaptureThread(RTSP_URL)
        if not cam.cap.isOpened():
            time.sleep(5)
            continue

        print("[IA] Câmera Conectada! Iniciando análise...")
        
        while True:
            frame = cam.read()
            if frame is None: break 

            bboxes, class_ids, contours, scores = segmentation_engine.detect(frame, imgsz=480, conf=0.20)
            frame_visual = frame.copy()
            
            tem_gancho = False
            tem_trava = False

            for bbox, class_id, contour in zip(bboxes, class_ids, contours):
                if segmentation_engine.classes is None: continue
                name = str(segmentation_engine.classes.get(class_id, "unknown")).lower()
                color = segmentation_engine.colors[class_id]
                
                if 'gancho' in name:
                    tem_gancho = True
                elif 'trava' in name or 'travado' in name:
                    tem_trava = True
                
                segmentation_engine.draw_mask(frame_visual, [contour], color, alpha=0.35)
                cv2.polylines(frame_visual, [contour], True, color, 2)

            status = "MONITORANDO"
            is_danger = False
            
            if tem_gancho:
                if tem_trava:
                    status = "TRAVADO"
                    is_danger = False
                    cv2.putText(frame_visual, "SEGURO", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
                else:
                    status = "DESTRAVADO"
                    is_danger = True
                    cv2.putText(frame_visual, "PERIGO", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)

            if status != last_arduino_status:
                try:

                    endpoint = f"{ARDUINO_URL}/lamp_interface"
                    dados = {"status": status}

                    requests.post(endpoint, json=dados, timeout=0.5)
                    print(f"[ARDUINO] Comando enviado: {status}")
                    last_arduino_status = status
                except Exception as e:
                    print("Erro ao comunicar com Arduino")

            global_status_data = {
                "status": status,
                "perigo": is_danger,
                "timestamp": time.time()
            }
            
            _, buffer = cv2.imencode('.jpg', frame_visual, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
            global_frame = buffer.tobytes()

        cam.release()
        time.sleep(2)

@app.on_event("startup")
def startup_event():
    threading.Thread(target=ai_loop, daemon=True).start()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.send_json(global_status_data)
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/video_feed")
def video_feed():
    def generate():
        while True:
            if global_frame:
                yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + global_frame + b'\r\n')
            time.sleep(0.04)
    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace;boundary=frame")

@app.get("api/status", response_model=ArduinoStatusResponse, tags=["Integração Arduino"])
def get_current_status():
    """
    Retorna o status atual da operação na Acearia.
    Ideal para o Arduino consultar (Polling) o estado das travas em tempo real.
    """
    return global_status_data
