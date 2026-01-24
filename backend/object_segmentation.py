import numpy as np
from ultralytics import YOLO
import random
import colorsys
import torch
import cv2

random.seed(2)

class ObjectSegmentation:
    def __init__(self, weights_path):
        self.weights_path = weights_path
        self.classes = None
        self.colors = self.random_colors(80)
        self.model = YOLO(self.weights_path)
        self.classes = self.model.names

        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
        elif torch.cuda.is_available():
            self.device = torch.device(0)
        else:
            self.device = torch.device("cpu")

    def random_colors(self, N, bright=False):
        brightness = 255 if bright else 180
        hsv = [(i / N + 1, 1, brightness) for i in range(N + 1)]
        colors = list(map(lambda c: colorsys.hsv_to_rgb(*c), hsv))
        random.shuffle(colors)
        return colors

    def draw_mask(self, img, pts, color, alpha=0.5):
        h, w, _ = img.shape
        overlay = img.copy()
        output = img.copy()
        cv2.fillPoly(overlay, pts, color)
        output = cv2.addWeighted(overlay, alpha, output, 1 - alpha, 0, output)
        return output

    def detect(self, img, imgsz=640, conf=0.25):
        height, width, channels = img.shape
        results = self.model.predict(source=img.copy(), imgsz=imgsz, conf=conf, save=False, save_txt=False)
        result = results[0]
        segmentation_contours_idx = []
        if result.masks is None:
            return [], [], [], []

        for seg in result.masks.xyn:
            seg[:, 0] *= width
            seg[:, 1] *= height
            segment = np.array(seg, dtype=np.int32)
            segmentation_contours_idx.append(segment)

        bboxes = np.array(result.boxes.xyxy.cpu(), dtype="int")
        class_ids = np.array(result.boxes.cls.cpu(), dtype="int")
        scores = np.array(result.boxes.conf.cpu(), dtype="float").round(2)
        return bboxes, class_ids, segmentation_contours_idx, scores
