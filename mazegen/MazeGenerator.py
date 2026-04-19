from dataclasses import dataclass
import random
from .ConfigLoader import AppConfig

Grid = list[bytearray]
Pos = tuple[int, int]

NORTH = 1 << 0
EAST = 1 << 1
SOUTH = 1 << 2
WEST = 1 << 3
WALL_42 = 1 << 4

ALL_WALLS = NORTH | EAST | SOUTH | WEST


@dataclass
class Maze:
    width: int
    height: int
    grid: Grid
    entry: Pos
    exit: Pos
    seed: int | None = None


class MazeGenerator:
    """Generate maze data for the visualizer-compatible cell grid."""

    @staticmethod
    def generate(config: "AppConfig") -> Maze:
        """Generate a maze from config."""
        if config.seed is not None:
            random.seed(config.seed)

        width = config.width
        height = config.height
        entry = config.entry
        exit = config.exit

        grid = MazeGenerator._init_grid(width, height)
        grid = MazeGenerator._embed_42_pattern(grid)
        grid = MazeGenerator._carve_passages(grid)

        if not config.perfect:
            grid = MazeGenerator._make_imperfect(grid)

        return Maze(
            width=width,
            height=height,
            grid=grid,
            entry=entry,
            exit=exit,
            seed=config.seed,
        )

    @staticmethod
    def _init_grid(width: int, height: int) -> Grid:
        """Initialize all cells as closed-wall cells."""
        return [
            bytearray(ALL_WALLS for _ in range(width)) for _ in range(height)
        ]

    @staticmethod
    def _embed_42_pattern(grid: Grid) -> Grid:
        """Embed protected '42' cells at the maze center.

        The 42 cells are treated as protected wall cells.
        """
        height = len(grid)
        width = len(grid[0])

        center_y = height // 2
        center_x = width // 2

        if height < 5 or width < 8:
            print('"42" pattern has omitted by the maze size.')
            return grid

        pattern = [
            (-2, -3),
            (-1, -3),
            (0, -3),
            (0, -2),
            (0, -1),
            (1, -1),
            (2, -1),
            (-2, 1),
            (-2, 2),
            (-2, 3),
            (-1, 3),
            (0, 1),
            (0, 2),
            (0, 3),
            (1, 1),
            (2, 1),
            (2, 2),
            (2, 3),
        ]

        for dy, dx in pattern:
            y = center_y + dy
            x = center_x + dx

            if 0 <= y < height and 0 <= x < width:
                grid[y][x] |= WALL_42

        return grid

    @staticmethod
    def _carve_passages(grid: Grid) -> Grid:
        """Generate maze passages using the Recursive Backtracker algorithm."""
        height = len(grid)
        width = len(grid[0])

        start = MazeGenerator._find_start_cell(grid)
        if start is None:
            raise ValueError(
                "No valid starting cell found for maze generation."
            )

        visited = [bytearray(width) for _ in range(height)]
        stack: list[Pos] = [start]
        visited[start[0]][start[1]] = True

        directions = [
            (-1, 0, NORTH, SOUTH),
            (0, 1, EAST, WEST),
            (1, 0, SOUTH, NORTH),
            (0, -1, WEST, EAST),
        ]

        while stack:
            y, x = stack[-1]
            neighbors: list[tuple[int, int, int, int]] = []

            for dy, dx, wall, opposite_wall in directions:
                ny, nx = y + dy, x + dx
                if not (0 <= ny < height and 0 <= nx < width):
                    continue
                if visited[ny][nx]:
                    continue
                if (grid[ny][nx] & WALL_42) != 0:
                    continue

                neighbors.append((ny, nx, wall, opposite_wall))

            if neighbors:
                ny, nx, wall, opposite_wall = random.choice(neighbors)
                grid[y][x] &= ~wall
                grid[ny][nx] &= ~opposite_wall
                visited[ny][nx] = True
                stack.append((ny, nx))
            else:
                stack.pop()

        return grid

    @staticmethod
    def _find_start_cell(grid: Grid) -> Pos | None:
        """Return the first cell that is not part of the 42 pattern."""
        height = len(grid)
        width = len(grid[0])

        for y in range(height):
            for x in range(width):
                if not MazeGenerator._is_42_cell(grid[y][x]):
                    return (y, x)
        return None

    @staticmethod
    def _make_imperfect(grid: Grid) -> Grid:
        """Break one wall to create an imperfect maze."""
        height = len(grid)
        width = len(grid[0])

        directions = [
            (-1, 0, NORTH, SOUTH),
            (0, 1, EAST, WEST),
            (1, 0, SOUTH, NORTH),
            (0, -1, WEST, EAST),
        ]

        candidates: list[tuple[int, int, int, int, int, int]] = []

        for y in range(height):
            for x in range(width):
                if MazeGenerator._is_42_cell(grid[y][x]):
                    continue

                for dy, dx, wall, opposite_wall in directions:
                    ny = y + dy
                    nx = x + dx

                    if not (0 <= ny < height and 0 <= nx < width):
                        continue
                    if MazeGenerator._is_42_cell(grid[ny][nx]):
                        continue

                    if (grid[y][x] & wall) == 0:
                        continue

                    candidates.append((y, x, ny, nx, wall, opposite_wall))

        random.shuffle(candidates)

        for y, x, ny, nx, wall, opposite_wall in candidates:
            grid[y][x] &= ~wall
            grid[ny][nx] &= ~opposite_wall

            min_y = max(0, min(y, ny) - 2)
            max_y = min(height - 3, max(y, ny))

            min_x = max(0, min(x, nx) - 2)
            max_x = min(width - 3, max(x, nx))

            bad = False

            for cy in range(min_y, max_y + 1):
                for cx in range(min_x, max_x + 1):
                    if MazeGenerator._is_open_3x3(grid, cy, cx):
                        bad = True
                        break
                if bad:
                    break

            if bad:
                grid[y][x] |= wall
                grid[ny][nx] |= opposite_wall
                continue

            return grid

        raise ValueError(
            "PERFECT = False but every removable wall creates a 3x3 open area."
        )

    @staticmethod
    def _is_open_3x3(grid: Grid, top_y: int, top_x: int) -> bool:
        """Check if a 3x3 block is fully open internally, ignoring the 42 pattern."""

        for y in range(top_y, top_y + 3):
            for x in range(top_x, top_x + 3):
                if MazeGenerator._is_42_cell(grid[y][x]):
                    return False

        for y in range(top_y, top_y + 3):
            for x in range(top_x, top_x + 2):
                if (grid[y][x] & EAST) != 0:
                    return False
                if (grid[y][x + 1] & WEST) != 0:
                    return False

        for y in range(top_y, top_y + 2):
            for x in range(top_x, top_x + 3):
                if (grid[y][x] & SOUTH) != 0:
                    return False
                if (grid[y + 1][x] & NORTH) != 0:
                    return False

        return True

    @staticmethod
    def _is_42_cell(cell: int) -> bool:
        """Return True if the cell is marked as a 42 protected cell."""
        return (cell & WALL_42) != 0
