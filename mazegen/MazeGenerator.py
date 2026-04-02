Grid = list[list[int]]


class MazeGenerator:
    """Generate maze."""

    @staticmethod
    def generate(config: "AppConfig") -> "Maze":
        grid = MazeGenerator._init_grid(config.width, config.height)
        grid = MazeGenerator._carve_passages(grid)
        grid = MazeGenerator._place_entry_exit(grid)
        grid = MazeGenerator._embed_42_pattern(grid)

        return Maze(grid=grid)

    @staticmethod
    def _init_grid(width: int, height: int) -> Grid:
        """Initialize grid."""
        raise NotImplementedError

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
