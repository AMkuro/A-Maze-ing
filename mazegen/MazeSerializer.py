from .MazeGenerator import Maze
from .MazeSolver import Solution

class MazeSerializer:
    """Serialize maze data into the project output format."""

    @staticmethod
    def serialize(maze: Maze, solution: Solution) -> str:
        """Return the final serialized maze output."""

    @staticmethod
    def _cell_to_hex(cell: int) -> str:
        """Convert one cell's lower 4 wall bits into a single hex digit."""

    @staticmethod
    def _format_grid(maze: Maze) -> list[str]:
        """Format the maze grid into hex-encoded row strings."""

    @staticmethod
    def _format_footer(maze: Maze, solution: Solution) -> list[str]:
        """Format footer lines required by the project output format."""

