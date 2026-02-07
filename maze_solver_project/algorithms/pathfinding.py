from collections import deque

class PathFinder:
    @staticmethod
    def bfs(binary_img, start, end):
        rows, cols = binary_img.shape
        neighbors = [(0, 1), (1, 0), (0, -1), (-1, 0)]

        queue = deque([start])
        came_from = {}
        visited = np.zeros(binary_img.shape, dtype=bool)
        visited[start] = True

        while queue:
            current = queue.popleft()
            if current == end:
                break

            for dx, dy in neighbors:
                neighbor = (current[0] + dx, current[1] + dy)
                if 0 <= neighbor[0] < rows and 0 <= neighbor[1] < cols:
                    if binary_img[neighbor] == 255 and not visited[neighbor]:
                        queue.append(neighbor)
                        visited[neighbor] = True
                        came_from[neighbor] = current
                        if neighbor == end:
                            return came_from

        return came_from
