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
        """Generate maze passages."""
        raise NotImplementedError

    @staticmethod
    def _place_entry_exit(grid: Grid) -> Grid:
        """Place entry and exit."""
        raise NotImplementedError

    @staticmethod
    def _embed_42_pattern(grid: Grid) -> Grid:
        """Embed 42 pattern."""
        raise NotImplementedError
