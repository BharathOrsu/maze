import pytest
from utils.validators import Validators

def test_image_validation():
    image = None
    with pytest.raises(ValueError):
        Validators.validate_image(image)
