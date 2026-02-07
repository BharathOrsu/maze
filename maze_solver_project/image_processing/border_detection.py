import cv2
import numpy as np

class BorderDetection:
    @staticmethod
    def detect_border(image):
        edges = cv2.Canny(image, threshold1=100, threshold2=200)
        return edges
