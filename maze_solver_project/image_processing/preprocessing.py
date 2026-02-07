import numpy as np
from PIL import Image

class ImagePreprocessor:
    @staticmethod
    def preprocess_image(img_path):
        img = np.asarray(Image.open(img_path).convert('L'))
        binary_img = (img > 128).astype(np.uint8) * 255
        return binary_img

    @staticmethod
    def resize_image(img, size=(512, 512)):
        return np.asarray(Image.fromarray(img).resize(size))
