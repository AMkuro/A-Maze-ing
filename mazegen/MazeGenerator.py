import random

Grid = list[list[int]]
Pos = tuple[int, int]

NORTH = 1 << 0
EAST = 1 << 1
SOUTH = 1 << 2
WEST = 1 << 3
WALL_42 = 1 << 4

ALL_WALLS = NORTH | EAST | SOUTH | WEST

class MazeGenerator:
    """Generate maze data for the visualizer-compatible cell grid."""

    @staticmethod
    def generate(config: AppConfig) -> Maze:
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
        grid = MazeGenerator._place_entry_exit(grid, entry, exit)

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
        return [[ALL_WALLS for _ in range(width)] for _ in range(height)]

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
            return grid

        pattern = [
            (-2, -3), (2, -3), (3, -3), (4, -3),
            (-2, -2), (4, -2),
            (-2, -1), (-1, -1), (0, -1),

            (2, -1), (3, -1), (4, -1),
            (0, 0), (2, 0),
            (0, 1), (2, 1), (3, 1), (4, 1)
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
            return grid

        visited = [[False for _ in range(width)] for _ in range(height)]
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
    def _place_entry_exit(
        grid: Grid,
        entry: Pos,
        exit: Pos,
    ) -> Grid:
        """Open the outer walls for entry and exit."""
        entry_y, entry_x = entry
        exit_y, exit_x = exit

        height = len(grid)
        width = len(grid[0])

        if entry_x == 0:
            grid[entry_y][entry_x] &= ~WEST
        elif entry_x == width - 1:
            grid[entry_y][entry_x] &= ~EAST
        elif entry_y == 0:
            grid[entry_y][entry_x] &= ~NORTH
        elif entry_y == height - 1:
            grid[entry_y][entry_x] &= ~SOUTH

        if exit_x == 0:
            grid[exit_y][exit_x] &= ~WEST
        elif exit_x == width - 1:
            grid[exit_y][exit_x] &= ~EAST
        elif exit_y == 0:
            grid[exit_y][exit_x] &= ~NORTH
        elif exit_y == height - 1:
            grid[exit_y][exit_x] &= ~SOUTH

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
    def _is_42_cell(cell: int) -> bool:
        """Return True if the cell is marked as a 42 protected cell."""
        return (cell & WALL_42) != 0
