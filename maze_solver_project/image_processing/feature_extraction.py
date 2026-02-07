import numpy as np
import cv2

class FeatureExtraction:
    @staticmethod
    def extract_features(image):
        contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return contours
