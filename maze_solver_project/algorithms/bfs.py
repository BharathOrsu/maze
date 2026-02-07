from algorithms.pathfinding import PathFinder

class BFS(PathFinder):
    @staticmethod
    def solve(binary_img, start, end):
        return PathFinder.bfs(binary_img, start, end)
