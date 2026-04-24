from .MazeModel import Maze, Solution


class MazeSerializer:
    """Serialize maze data into the project output format."""

    @staticmethod
    def serialize(maze: Maze, solution: Solution) -> str:
        """Return the final serialized maze output.

        Args:
            maze: Maze to serialize.
            solution: Shortest path solution for the maze.

        Returns:
            Complete output file content ending with a newline.
        """
        grid_lines = MazeSerializer._format_grid(maze)
        footer_lines = MazeSerializer._format_footer(maze, solution)
        lines = grid_lines + [""] + footer_lines
        return "\n".join(lines) + "\n"

    @staticmethod
    def _cell_to_hex(cell: int) -> str:
        """Convert one cell's lower 4 wall bits to one hex digit.

        Args:
            cell: Encoded cell value.

        Returns:
            Uppercase hexadecimal digit for the wall bits.
        """
        val = cell & 0x0F
        return format(val, "X")

    @staticmethod
    def _format_grid(maze: Maze) -> list[str]:
        """Format the maze grid into hex-encoded row strings.

        Args:
            maze: Maze to format.

        Returns:
            One hexadecimal string per maze row.
        """
        lines: list[str] = []

        for row in maze.grid:
            line = "".join(MazeSerializer._cell_to_hex(cell) for cell in row)
            lines.append(line)

        return lines

    @staticmethod
    def _format_footer(maze: Maze, solution: Solution) -> list[str]:
        """Format footer lines required by the project output format.

        Args:
            maze: Maze whose entry and exit are written.
            solution: Solution whose movement string is written.

        Returns:
            Entry coordinates, exit coordinates, and solution movement string.
        """
        entry_y, entry_x = maze.entry
        exit_y, exit_x = maze.exit

        return [
            f"{entry_x},{entry_y}",
            f"{exit_x},{exit_y}",
            solution.news,
        ]
