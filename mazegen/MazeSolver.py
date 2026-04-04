from collections import deque
from .MazeGenerator import NORTH, EAST, SOUTH, WEST, Maze
from dataclasses import dataclass

Pos = tuple[int, int]


@dataclass
class Solution:
    path: list[Pos]
    news: str


class MazeSolver:
    """Solve a maze using BFS."""

    @staticmethod
    def solve(maze: "Maze") -> "Solution":
        start: Pos = maze.entry
        end: Pos = maze.exit

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

        queue = deque()
        queue.append((start[0], start[1]))
        grid = maze.grid
        came_from: dict[Pos, Pos | None] = {start: None}

        directions = [
            (-1, 0, NORTH),
            (1, 0, SOUTH),
            (0, -1, WEST),
            (0, 1, EAST),
        ]

        while queue:
            y, x = queue.popleft()

            if (y, x) == end:
                break

            for dy, dx, direction in directions:
                ny, nx = y + dy, x + dx
                neighbor: Pos = (ny, nx)

                if neighbor in came_from:
                    continue

                if 0 <= ny < maze.height and 0 <= nx < maze.width:
                    if grid[y][x] & direction == direction:
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

        path: list[Pos] = [end]
        curr: Pos = end

        while curr != start:
            prev = came_from[curr]
            if prev is None:
                raise ValueError("Invalid path data")
            path.append(prev)
            curr = prev

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
