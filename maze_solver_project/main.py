from image_processing.preprocessing import ImagePreprocessor
from algorithms.pathfinding import PathFinder
from utils.logger import Logger
from utils.config import Config

def main():
    Logger.setup()
    config = Config()

    img_path = "path/to/image.png"
    binary_img = ImagePreprocessor.preprocess_image(img_path)
    start, end = (0, 0), (19, 19)
    came_from = PathFinder.bfs(binary_img, start, end)

    if came_from:
        Logger.log("Maze solved successfully.")
    else:
        Logger.log("No solution found.", level="error")

if __name__ == "__main__":
    main()
