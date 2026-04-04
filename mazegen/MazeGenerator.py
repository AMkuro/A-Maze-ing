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

        grid = MazeGenerator._init_grid(width, height)
        grid = MazeGenerator._embed_42_pattern(grid)
        grid = MazeGenerator._carve_passages(grid)
        grid, entry, exit = MazeGenerator._place_entry_exit(grid)

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
        They do not need to connect to the maze passages.
        """
        height = len(grid)
        width = len(grid[0])

        center_y = height // 2
        center_x = width // 2

        if height < 5 or width < 8:
            return grid

        pattern = [
            # "4"
            (-2, -3),
            (-1, -3),
            (0, -3),
            (0, -2),
            (-2, -1),
            (-1, -1),
            (0, -1),
            (1, -1),
            # "2"
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

        stack: list[Pos] = []

        start = (1, 1)
        grid[1][1] = PASSAGE
        stack.append(start)

        directions = [(-2, 0), (2, 0), (0, -2), (0, 2)]

        while stack:
            y, x = stack[-1]

            neighbors = []

            for dy, dx in directions:
                ny = y + dy
                nx = x + dx

                if 0 < ny < height and 0 < nx < width:
                    if grid[ny][nx] == WALL:
                        neighbors.append((ny, nx, dy, dx))

            if neighbors:
                ny, nx, dy, dx = random.choice(neighbors)

                grid[y + dy // 2][x + dx // 2] = PASSAGE
                grid[ny][nx] = PASSAGE

                stack.append((ny, nx))
            else:
                stack.pop()

        return grid

    @staticmethod
    def _place_entry_exit(grid: Grid) -> Grid:
        """Place maze entry and exit."""
        height = len(grid)
        width = len(grid[0])

        grid[1][0] = PASSAGE
        grid[height - 2][width - 1] = PASSAGE

        return grid

    @staticmethod
    def _find_entry(grid: Grid) -> Pos:
        for y in range(len(grid)):
            if grid[y][0] == PASSAGE:
                return (y, 0)
        raise ValueError("Entry not found")

    @staticmethod
    def _find_exit(grid: Grid) -> Pos:
        width = len(grid[0])
        for y in range(len(grid)):
            if grid[y][width - 1] == PASSAGE:
                return (y, width - 1)
        raise ValueError("Exit not found")
