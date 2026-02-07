class Validators:
    @staticmethod
    def validate_image(image):
        if image is None:
            raise ValueError("Image cannot be None.")
        return True
