import pytest
import numpy as np
from algorithms.pathfinding import PathFinder
from image_processing.preprocessing import ImagePreprocessor

def test_bfs():
    img = np.zeros((20, 20))
    img[0, 1] = 255  # Start
    img[19, 19] = 255  # End
    start = (0, 1)
    end = (19, 19)
    came_from = PathFinder.bfs(img, start, end)
    assert came_from is not None
