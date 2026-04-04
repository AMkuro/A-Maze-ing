import random

Grid = list[list[int]]
Pos = tuple[int, int]

WALL = 1
PASSAGE = 0

class MazeGenerator:
    """Generate maze."""

    @staticmethod
    def generate(config: "AppConfig") -> "Maze":
        grid = MazeGenerator._init_grid(config.width, config.height)
        grid = MazeGenerator._carve_passages(grid)
        grid = MazeGenerator._place_entry_exit(grid)
        grid = MazeGenerator._embed_42_pattern(grid)

        entry = MazeGenerator._find_entry(grid)
        exit = MazeGenerator._find_exit(grid)

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
        """Initialize grid filled with walls."""
        grid_height = height * 2 + 1
        grid_width = width * 2 + 1

        return [[WALL for _ in range(grid_width)] for _ in range(grid_height)]

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
    def _embed_42_pattern(grid: Grid) -> Grid:
        """Embed 42 pattern."""
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
