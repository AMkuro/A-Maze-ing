from collections import deque

Pos = tuple[int, int]


class MazeSolver:
    """Solve a maze using BFS."""

    @staticmethod
    def solve(maze: "Maze") -> "Solution":
        start: Pos = maze.start
        end: Pos = maze.end

        came_from = MazeSolver._bfs(maze, start, end)

        if end not in came_from:
            raise ValueError("Maze has no solution")

        path = MazeSolver._reconstruct_path(came_from, start, end)
        news = MazeSolver._to_news_string(path)

        return Solution(path, news)

    @staticmethod
    def _bfs(
        maze: "Maze",
        start: Pos,
        end: Pos,
    ) -> dict[Pos, Pos | None]:

        queue = deque([start])
        came_from: dict[Pos, Pos | None] = {start: None}

        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        while queue:
            y, x = queue.popleft()

            if (y, x) == end:
                break

            for dy, dx in directions:
                ny = y + dy
                nx = x + dx
                neighbor: Pos = (ny, nx)

                if neighbor in came_from:
                    continue

                if not maze.is_open(ny, nx):
                    continue

                queue.append(neighbor)
                came_from[neighbor] = (y, x)

        return came_from

    @staticmethod
    def _reconstruct_path(
        came_from: dict[Pos, Pos | None],
        start: Pos,
        end: Pos,
    ) -> list[Pos]:

        path: list[Pos] = []
        current: Pos | None = end

        while current is not None:
            path.append(current)
            current = came_from[current]

        path.reverse()
        return path

    @staticmethod
    def _to_news_string(path: list[Pos]) -> str:
        moves: list[str] = []

        for i in range(1, len(path)):
            y1, x1 = path[i - 1]
            y2, x2 = path[i]

            dy = y2 - y1
            dx = x2 - x1

            if dy == -1:
                moves.append("N")
            elif dy == 1:
                moves.append("S")
            elif dx == 1:
                moves.append("E")
            elif dx == -1:
                moves.append("W")

        return "".join(moves)
