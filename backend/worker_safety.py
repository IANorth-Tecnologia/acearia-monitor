import cv2
import redis
import json
import os
import time
import threading
import queue
import numpy as np
from object_segmentation import ObjectSegmentation

DEFAULT_RTSP = "rtsp://admin:eletricasnb2021@10.6.51.75:554/cam/realmonitor?channel=1&subtype=1"
RTSP_URL = os.getenv("RTSP_URL", DEFAULT_RTSP)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
MODEL_PATH = "models/pan28.pt"

class VideoCaptureThread:
    def __init__(self, src):
        self.src = src
        self.cap = cv2.VideoCapture(self.src)
        self.q = queue.Queue(maxsize=1) 
        self.stopped = False
        self.connected = self.cap.isOpened()
        if self.connected:
            self.thread = threading.Thread(target=self._reader, daemon=True)
            self.thread.start()

    def _reader(self):
        while not self.stopped:
            ret, frame = self.cap.read()
            if not ret:
                self.stopped = True
                break
            if not self.q.empty():
                try: self.q.get_nowait()
                except queue.Empty: pass
            self.q.put(frame)

    def read(self):
        try: return self.q.get(timeout=2.0) 
        except queue.Empty: return None 

    def release(self):
        self.stopped = True
        if self.connected: self.cap.release()

def run():
    try:
        r = redis.Redis(host=REDIS_HOST, port=6379, db=0)
        r.ping()
        print(f"[WORKER] Conectado ao Redis em {REDIS_HOST}")
    except Exception as e:
        print(f"[WORKER] Erro Redis: {e}")
        return

    print(f"[WORKER] Carregando modelo SEGMENTATION: {MODEL_PATH}")
    try:
        segmentation_engine = ObjectSegmentation(MODEL_PATH)
    except Exception as e:
        print(f"[WORKER] Erro Fatal no Modelo: {e}")
        return

    while True:
        print(f"[WORKER] Conectando câmera...")
        cam = VideoCaptureThread(RTSP_URL)
        
        if not cam.connected:
            print("[WORKER] Falha. Tentando em 5s...")
            cam.release()
            time.sleep(5)
            continue

        print("[WORKER] Online! Usando Segmentação...")
        
        while True:
            frame = cam.read()
            if frame is None: break 

            # Configurações de Inferência
            bboxes, class_ids, contours, scores = segmentation_engine.detect(frame, imgsz=640, conf=0.25)
            
            frame_visual = frame.copy()
            
            ganchos = []
            suportes = []
            travas = []
            panelas = []

            for bbox, class_id, contour, score in zip(bboxes, class_ids, contours, scores):
                try:
                    classes_dict = segmentation_engine.classes
                    if classes_dict is None:
                        continue 
                    
                    raw_name = classes_dict.get(class_id, "unknown")
                    name = str(raw_name).lower()
                    
                    color = segmentation_engine.colors[class_id] if class_id < len(segmentation_engine.colors) else (255, 255, 255)
                    
                    x1, y1, x2, y2 = bbox
                    cx = int((x1 + x2) / 2)
                    cy = int((y1 + y2) / 2)
                    
                    obj_data = {
                        'box': bbox, 
                        'contour': contour, 
                        'center': (float(cx), float(cy)) 
                    }

                    if 'gancho' in name:
                        ganchos.append(obj_data); color = (0, 0, 255)
                    elif 'suportepanela' in name:
                        suportes.append(obj_data); color = (255, 0, 0)
                    elif 'trava' in name or 'travado' in name:
                        travas.append(obj_data); color = (0, 255, 0)
                    elif 'panela' in name or 'forno' in name:
                        panelas.append(obj_data)

                    segmentation_engine.draw_mask(frame_visual, [contour], color, alpha=0.4)
                    cv2.polylines(frame_visual, [contour], True, color, 2)
                    
                    cv2.putText(frame_visual, name.upper(), (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                except Exception: 
                    continue


            status = "MONITORANDO"
            is_safe = True
            
            if len(ganchos) > 0 and len(suportes) > 0:
                acoplado = False
                
                for g in ganchos:
                    g_center = g['center'] 
                    
                    for s in suportes:
                        # Verifica se o centro do gancho está dentro do SUPORTE
                        if cv2.pointPolygonTest(s['contour'], g_center, False) >= 0:
                            acoplado = True
                            break
                    if acoplado: break
                
                if acoplado:
                    # Se acoplou, procura a trava
                    if len(travas) > 0:
                        status = "SEGURO: TRAVADO"
                        is_safe = True
                        cv2.putText(frame_visual, "SEGURO", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
                    else:
                        status = "PERIGO: SEM TRAVA"
                        is_safe = False
                        cv2.putText(frame_visual, "PERIGO", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
                else:
                    status = "APROXIMACAO"
            
            elif len(ganchos) > 0: status = "MOVIMENTACAO"

            try:
                _, buffer = cv2.imencode('.jpg', frame_visual, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
                r.set("live_frame", buffer.tobytes())
                
                packet = {
                    "status": status,
                    "perigo": not is_safe,
                    "panelas": len(panelas),
                    "garras": len(ganchos),
                    "travas": len(travas),
                    "timestamp": time.time()
                }
                r.publish("safety_alerts", json.dumps(packet))
            except: pass

        cam.release()
        time.sleep(2)

if __name__ == "__main__":
    run()
