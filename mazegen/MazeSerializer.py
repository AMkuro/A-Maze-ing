from .MazeGenerator import Maze
from .MazeSolver import Solution

class MazeSerializer:
    """Serialize maze data into the project output format."""

    @staticmethod
    def serialize(maze: Maze, solution: Solution) -> str:
        """Return the final serialized maze output."""
        grid_lines = MazeSerializer._format_grid(maze)
        footer_lines = MazeSerializer._format_footer(maze, solution)
        lines = grid_lines + [""] + footer_lines
        return "\n".join(lines) + "\n"

    @staticmethod
    def _cell_to_hex(cell: int) -> str:
        """Convert one cell's lower 4 wall bits into a single hex digit."""
        val = cell & 0x0F
        return format(val, "X")

    @staticmethod
    def _format_grid(maze: Maze) -> list[str]:
        """Format the maze grid into hex-encoded row strings."""
        lines: list[str] = []

        for row in maze.grid:
            line = "".join(MazeSerializer._cell_to_hex(cell) for cell in row)
            lines.append(line)

        return lines


    @staticmethod
    def _format_footer(maze: Maze, solution: Solution) -> list[str]:
        """Format footer lines required by the project output format."""
        entry_y, entry_x = maze.entry
        exit_y, exit_x = maze.exit

        return [
            f"{entry_x},{entry_y}",
            f"{exit_x},{exit_y}",
            solution.news,
        ]
