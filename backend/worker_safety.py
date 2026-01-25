import cv2
import redis
import json
import os
import time
import numpy as np
from object_segmentation import ObjectSegmentation

DEFAULT_RTSP = "rtsp://admin:eletricasnb2021@10.6.51.75:554/cam/realmonitor?channel=1&subtype=1"
RTSP_URL = os.getenv("RTSP_URL", DEFAULT_RTSP)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
MODEL_PATH = "models/pan28.pt"

CLASS_ID_PANELA = 0
CLASS_ID_GARRA = 1

def run():
    try:
        r = redis.Redis(host=REDIS_HOST, port=6379, db=0)
        r.ping()
        print(f"[WORKER] Conectado ao Redis em {REDIS_HOST}")
    except Exception as e:
        print(f"[WORKER] ERRO: Redis inacessível. {e}")
        return

    print(f"[WORKER] Inicializando Segmentação: {MODEL_PATH}")
    try:
        segmentation_engine = ObjectSegmentation(MODEL_PATH)
        print("[WORKER] Modelo carregado.")
    except Exception as e:
        print(f"[WORKER] Erro modelo: {e}. Usando fallback.")
        segmentation_engine = ObjectSegmentation("yolov8n-seg.pt")

    while True:
        print(f"[WORKER] Conectando câmera: {RTSP_URL}")
        cap = cv2.VideoCapture(RTSP_URL)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not cap.isOpened():
            print("[WORKER] Erro câmera. Retry 5s...")
            time.sleep(5)
            continue

        while True:
            success, frame = cap.read()
            if not success:
                print("[WORKER] Frame drop. Reiniciando...")
                break

            bboxes, class_ids, contours, scores = segmentation_engine.detect(frame, conf=0.5)
            
            frame_visual = frame.copy()
            panelas_box = []
            garras_box = []

            for bbox, class_id, contour, score in zip(bboxes, class_ids, contours, scores):
                color = segmentation_engine.colors[class_id]
                frame_visual = segmentation_engine.draw_mask(frame_visual, [contour], color, alpha=0.4)
                
                x, y, x2, y2 = bbox
                cv2.rectangle(frame_visual, (x, y), (x2, y2), color, 2)
                name = segmentation_engine.classes[class_id]
                cv2.putText(frame_visual, f"{name}", (x, y - 10), cv2.FONT_HERSHEY_PLAIN, 1.5, color, 2)

                if class_id == CLASS_ID_PANELA: panelas_box.append(bbox)
                elif class_id == CLASS_ID_GARRA: garras_box.append(bbox)

            status = "MONITORANDO"
            perigo = False
            
            if len(panelas_box) > 0:
                encaixes = 0
                for px1, py1, px2, py2 in panelas_box:
                    panela_area = (px2 - px1) * (py2 - py1)
                    for gx1, gy1, gx2, gy2 in garras_box:
                        ix1 = max(px1, gx1); iy1 = max(py1, gy1)
                        ix2 = min(px2, gx2); iy2 = min(py2, gy2)
                        inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
                        if inter > (panela_area * 0.1): encaixes += 1

                if len(garras_box) == 0:
                    status = "PERIGO: CARGA SOLTA"
                    perigo = True
                elif encaixes == 0:
                    status = "ATENÇÃO: DESALINHADO"
                    perigo = True
                else:
                    status = "SEGURO: ACOPLADO"
                    perigo = False

            _, buffer = cv2.imencode('.jpg', frame_visual)
            r.set("live_frame", buffer.tobytes())
            r.publish("safety_alerts", json.dumps({
                "status": status, 
                "mensagem": f"P: {len(panelas_box)} | G: {len(garras_box)}", 
                "perigo": perigo,
                "panelas": len(panelas_box),
                "garras": len(garras_box)
            }))

        cap.release()

if __name__ == "__main__":
    run()
