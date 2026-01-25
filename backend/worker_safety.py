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
        self.cap = cv2.VideoCapture(src)
        self.q = queue.Queue(maxsize=1) 
        self.stopped = False
        self.thread = threading.Thread(target=self._reader, daemon=True)
        self.thread.start()

    def _reader(self):
        while not self.stopped:
            ret, frame = self.cap.read()
            if not ret: 
                break
            if not self.q.empty():
                try: 
                    self.q.get_nowait() 
                except queue.Empty: 
                    pass
            self.q.put(frame)

    def read(self):
        return self.q.get() 

    def release(self):
        self.stopped = True
        self.cap.release()



def run():
    try:
        r = redis.Redis(host=REDIS_HOST, port=6379, db=0)
        r.ping()
        print(f"[WORKER] Conectado ao Redis em {REDIS_HOST}")
    except Exception as e:
        print(f"[WORKER] ERRO CRÍTICO: Redis inacessível. {e}")
        return

    print(f"[WORKER] Carregando IA: {MODEL_PATH}")
    try:
        segmentation_engine = ObjectSegmentation(MODEL_PATH)

        print("[WORKER] Modelo carregado com sucesso.")
    except Exception as e:
        print(f"[WORKER] Erro ao carregar modelo: {e}")
        return

    print(f"[WORKER] Iniciando stream: {RTSP_URL}")
    cam = VideoCaptureThread(RTSP_URL)




    while True:
        #cap = cv2.VideoCapture(RTSP_URL)

        frame = cam.read()
        if frame is None: continue
        
        
        while True:
            success, frame = cam.read()
            if not success:
                print("[WORKER] Perda de sinal de vídeo.")
                break

            bboxes, class_ids, contours, scores = segmentation_engine.detect(frame, imgsz=320, conf=0.25)
            frame_visual = frame.copy()
            
            ganchos = []
            suportes = []
            travas = []
            panelas = []

            for bbox, class_id, contour, score in zip(bboxes, class_ids, contours, scores):
                raw_name = str(segmentation_engine.classes)[class_id]
                name = str(raw_name).lower()
                
                color = segmentation_engine.colors[class_id]
                label = name

                if 'gancho' in name:
                    ganchos.append(bbox)
                    label = "GANCHO"
                    color = (0, 0, 255) 
                elif 'suportepanela' in name:
                    suportes.append(bbox)
                    label = "SUPORTE"
                    color = (255, 0, 0) 
                elif 'trava' in name or 'travado' in name: 
                    travas.append(bbox)
                    label = "TRAVA"
                    color = (0, 255, 0) 
                elif 'panela' in name or 'forno' in name:
                    panelas.append(bbox)
                    label = "PANELA"

                x, y, x2, y2 = bbox
                segmentation_engine.draw_mask(frame_visual, [contour], color, alpha=0.3)
                cv2.rectangle(frame_visual, (x, y), (x2, y2), color, 2)
                cv2.putText(frame_visual, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            status = "AGUARDANDO"
            is_safe = True
            mensagem_detalhe = "Monitorando área..."

            if len(ganchos) > 0 and len(suportes) > 0:
                acoplados = 0
                travados_corretamente = 0
                
                for gx1, gy1, gx2, gy2 in ganchos:
                    for sx1, sy1, sx2, sy2 in suportes:
                        ix1 = max(gx1, sx1); iy1 = max(gy1, sy1)
                        ix2 = min(gx2, sx2); iy2 = min(gy2, sy2)
                        inter_area = max(0, ix2 - ix1) * max(0, iy2 - iy1)
                        
                        if inter_area > 0:
                            acoplados += 1
                            
                            busca_x1, busca_y1 = min(gx1, sx1) - 50, min(gy1, sy1) - 50
                            busca_x2, busca_y2 = max(gx2, sx2) + 50, max(gy2, sy2) + 50
                            
                            for tx1, ty1, tx2, ty2 in travas:
                                t_center_x = (tx1 + tx2) / 2
                                t_center_y = (ty1 + ty2) / 2
                                if (busca_x1 < t_center_x < busca_x2) and (busca_y1 < t_center_y < busca_y2):
                                    travados_corretamente += 1

                if acoplados > 0:
                    if travados_corretamente > 0:
                        status = "SEGURO: TRAVADO"
                        mensagem_detalhe = "Gancho acoplado e trava detectada."
                        is_safe = True
                        cv2.putText(frame_visual, "SEGURO", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 4)
                    else:
                        status = "PERIGO: DESTRAVADO"
                        mensagem_detalhe = "ATENÇÃO: Gancho sem trava de segurança!"
                        is_safe = False
                        cv2.putText(frame_visual, "PERIGO", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 4)
                else:
                    status = "APROXIMAÇÃO"
                    mensagem_detalhe = "Gancho próximo ao suporte."

            elif len(ganchos) > 0:
                status = "MOVIMENTAÇÃO"
                mensagem_detalhe = "Gancho em movimento."

            _, buffer = cv2.imencode('.jpg', frame_visual)
            try:
                r.set("live_frame", buffer.tobytes())
                
                packet = {
                    "status": status,
                    "mensagem": mensagem_detalhe,
                    "perigo": not is_safe,
                    "panelas": len(panelas),
                    "garras": len(ganchos), 
                    "travas": len(travas),
                    "timestamp": time.time()
                }
                r.publish("safety_alerts", json.dumps(packet))
            except Exception as e:
                print(f"[WORKER] Erro Redis: {e}")

            time.sleep(0.033)

        cam.release()
        print("[WORKER] Reiniciando conexão...")

if __name__ == "__main__":
    run()
