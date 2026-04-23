from dataclasses import dataclass
from .MazeModel import Maze, Solution, Wall
import sys
from typing import Callable

RESET = "\033[0m"


@dataclass
class ColorScheme:
    """ANSI color prefixes used by the terminal visualizer.

    Attributes:
        wall: Foreground or background prefix for walls.
        path: Background prefix for open-path cells.
        solution: Background prefix for solution-path cells.
        entry: Background prefix for the entry cell.
        exit: Background prefix for the exit cell.
    """

    wall: str = ""
    path: str = ""
    solution: str = "\033[48;2;56;73;225m"
    entry: str = "\033[48;2;50;200;80m"
    exit: str = "\033[48;2;220;70;60m"

    @staticmethod
    def fg(r: int, g: int, b: int) -> str:
        """Build a 24-bit ANSI foreground color prefix.

        Args:
            r: Red channel from 0 to 255.
            g: Green channel from 0 to 255.
            b: Blue channel from 0 to 255.

        Returns:
            ANSI escape prefix for the requested foreground color.
        """
        return f"\033[38;2;{r};{g};{b}m"

    @staticmethod
    def bg(r: int, g: int, b: int) -> str:
        """Build a 24-bit ANSI background color prefix.

        Args:
            r: Red channel from 0 to 255.
            g: Green channel from 0 to 255.
            b: Blue channel from 0 to 255.

        Returns:
            ANSI escape prefix for the requested background color.
        """
        return f"\033[48;2;{r};{g};{b}m"

    @staticmethod
    def fg256(n: int) -> str:
        """Build a 256-color ANSI foreground prefix.

        Args:
            n: ANSI 256-color palette index.

        Returns:
            ANSI escape prefix for the requested foreground color.
        """
        return f"\033[38;5;{n}m"

    @staticmethod
    def bg256(n: int) -> str:
        """Build a 256-color ANSI background prefix.

        Args:
            n: ANSI 256-color palette index.

        Returns:
            ANSI escape prefix for the requested background color.
        """
        return f"\033[48;5;{n}m"


class Visualizer:
    """Render a maze and its solution in the terminal."""

    def __init__(
        self,
        maze: Maze,
        solution: Solution,
        show_path: bool = False,
    ) -> None:
        """Initialize a visualizer.

        Args:
            maze: Maze to render.
            solution: Solution path for the maze.
            show_path: Whether to show the solution path initially.
        """
        self._maze = maze
        self._solution = solution
        self._show_path: bool = show_path
        self._color_scheme: ColorScheme = ColorScheme()
        self._render_ratio_cache: (
            tuple[
                list[tuple[int | None, int | None]],
                list[tuple[int | None, int | None]],
            ]
            | None
        ) = None
        self._char_grid_cache: list[list[str]] | None = None
        self._idx_grid_cache: list[bytearray] | None = None

    def _make_src_pairs(
        self,
        size: int,
        even_repeat: int,
        odd_repeat: int,
    ) -> list[tuple[int | None, int | None]]:
        """Build source-index pairs for half-block rendering.

        Args:
            size: Number of source rows or columns.
            even_repeat: Repetition count for wall positions.
            odd_repeat: Repetition count for cell interior positions.

        Returns:
            Pairs of source indexes. ``None`` represents empty padding.
        """
        expanded: list[int | None] = []

        for i in range(size):
            repeat = even_repeat if i % 2 == 0 else odd_repeat
            for _ in range(repeat):
                expanded.append(i)

        if len(expanded) % 2 == 1:
            expanded.append(None)

        pairs: list[tuple[int | None, int | None]] = []
        for i in range(0, len(expanded), 2):
            pairs.append((expanded[i], expanded[i + 1]))
        return pairs

    def _get_render_pairs(
        self,
    ) -> tuple[
        list[tuple[int | None, int | None]],
        list[tuple[int | None, int | None]],
    ]:
        """Return cached source-index pairs for rows and columns.

        Returns:
            Row and column source-index pairs used for half-block rendering.
        """
        if self._render_ratio_cache is None:
            src_rows = 2 * self._maze.height + 1
            src_cols = 2 * self._maze.width + 1
            row_pairs = self._make_src_pairs(
                src_rows,
                even_repeat=1,
                odd_repeat=2,
            )
            col_pairs = self._make_src_pairs(
                src_cols,
                even_repeat=1,
                odd_repeat=5,
            )
            self._render_ratio_cache = (row_pairs, col_pairs)

        return self._render_ratio_cache

    def _build_render_buffer(self) -> list[bytearray]:
        """Build a binary wall canvas from the maze grid.

        Returns:
            Buffer where nonzero values represent wall pixels.
        """
        maze = self._maze
        w, h = maze.width, maze.height
        grid = maze.grid

        t_row = 2 * h + 1
        t_col = 2 * w + 1
        # bytearray combines
        # mutability with a contiguous memory layout,
        # so it's faster then bytes and list.
        canvas: list[bytearray] = [bytearray(t_col) for _ in range(t_row)]

        set_of_wall = b"\x01\x01\x01"

        for r in range(h):
            grid_row = grid[r]
            top = 2 * r
            center_r = top + 1
            bottom = top + 2

            row_top = canvas[top]
            row_center = canvas[center_r]
            row_bottom = canvas[bottom]
            for c in range(w):
                cell = grid_row[c]
                left = 2 * c

                # North Wall
                if cell & Wall.NORTH:
                    row_top[left:left + 3] = set_of_wall

                # West Wall
                if cell & Wall.WEST:
                    row_top[left] = 1
                    row_center[left] = 1
                    row_bottom[left] = 1

        # The last row for setting South Wall
        last_grid_row = grid[h - 1]
        last_canvas_row = canvas[-1]
        for c in range(w):
            if last_grid_row[c] & Wall.SOUTH:
                left = 2 * c
                last_canvas_row[left:left + 3] = set_of_wall

        # The last column for setting East Wall
        right_col = -1
        for r in range(h):
            if grid[r][w - 1] & Wall.EAST:
                top = 2 * r
                center_r = top + 1
                bottom = top + 2
                canvas[top][right_col] = 1
                canvas[center_r][right_col] = 1
                canvas[bottom][right_col] = 1
        return canvas

    def _build_space_grid_and_idx(
        self, buffer: list[bytearray]
    ) -> tuple[list[list[str]], list[bytearray]]:
        row_pairs, col_pairs = self._get_render_pairs()

    def _build_char_grid_and_idx(
        self, buffer: list[bytearray]
    ) -> tuple[list[list[str]], list[bytearray]]:
        """Convert a binary wall buffer to terminal block characters.

        Args:
            buffer: Binary wall canvas produced by ``_build_render_buffer``.

        Returns:
            Render characters and matching lookup indexes.
        """
        LOOKUP: tuple[str, ...] = (
            " ",
            "▗",
            "▖",
            "▄",
            "▝",
            "▐",
            "▞",
            "▟",
            "▘",
            "▚",
            "▌",
            "▙",
            "▀",
            "▜",
            "▛",
            "█",
        )

        row_pairs, col_pairs = self._get_render_pairs()

        src_cols = len(buffer[0])
        zero_row = b"\x00" * src_cols

        char_grid: list[list[str]] = []
        idx_grid: list[bytearray] = []

        for top_src, bottom_src in row_pairs:
            top_row = zero_row if top_src is None else buffer[top_src]
            bottom_row = zero_row if bottom_src is None else buffer[bottom_src]

            chars: list[str] = []
            idx_row = bytearray()

            for left_src, right_src in col_pairs:
                tl = 0 if left_src is None else top_row[left_src]
                tr = 0 if right_src is None else top_row[right_src]
                bl = 0 if left_src is None else bottom_row[left_src]
                br = 0 if right_src is None else bottom_row[right_src]

                idx = (
                    ((tl != 0) << 3)
                    | ((tr != 0) << 2)
                    | ((bl != 0) << 1)
                    | (br != 0)
                )

                idx_row.append(idx)
                chars.append(LOOKUP[idx])
            idx_grid.append(idx_row)
            char_grid.append(chars)

        return char_grid, idx_grid

    def _apply_color(
        self,
        char_grid: list[list[str]],
        idx_grid: list[bytearray],
    ) -> str:
        """Apply ANSI colors to rendered characters.

        Args:
            char_grid: Render characters.
            idx_grid: Lookup indexes for the rendered characters.

        Returns:
            Colored terminal string without a trailing newline.
        """
        wall_pre = self._color_scheme.wall
        path_pre = self._color_scheme.path
        entry_pre = self._color_scheme.entry
        exit_pre = self._color_scheme.exit
        solution_pre = self._color_scheme.solution
        row_pairs, col_pairs = self._get_render_pairs()

        rows = len(char_grid)
        cols = len(char_grid[0]) if rows > 0 else 0

        highlight: list[list[str]] = [[""] * cols for _ in range(rows)]

        cells_to_highlight = [
            (pos, solution_pre) for pos in self._solution.path
        ] + [
            (self._maze.entry, entry_pre),
            (self._maze.exit, exit_pre),
        ]
        for (mr, mc), color in cells_to_highlight:
            if not color:
                continue
            if color == solution_pre and not self._show_path:
                continue
            target_row = 2 * mr + 1
            target_col = 2 * mc + 1
            out_rows = [
                r
                for r, (top_src, bottom_src) in enumerate(row_pairs)
                if top_src == target_row or bottom_src == target_row
            ]
            out_cols = [
                c
                for c, (left_src, right_src) in enumerate(col_pairs)
                if left_src == target_col or right_src == target_col
            ]
            for r in out_rows:
                hrow = highlight[r]
                for c in out_cols:
                    hrow[c] = color
        lines: list[str] = []
        last_row = rows - 1
        last_col = cols - 1
        for r in range(rows):
            out_row: list[str] = []
            chars = char_grid[r]
            vals = idx_grid[r]
            hrow = highlight[r]
            current_pre: str = ""
            for c in range(cols):
                v = vals[c]
                hl = hrow[c]
                suppress_bg = (c == last_col and (v & 0b1010) == 0b1010) or (
                    r == last_row and (v & 0b1000) == 0b1000
                )
                bg = "" if suppress_bg else (hl or path_pre)
                pre = (bg + wall_pre) if v != 0 else bg
                if pre != current_pre:
                    if current_pre:
                        out_row.append(RESET)
                    if pre:
                        out_row.append(pre)
                    current_pre = pre
                out_row.append(chars[c])
            if current_pre:
                out_row.append(RESET)
            lines.append("".join(out_row))
        return "\n".join(lines)

    def _render_to_string(self, buffer: list[bytearray]) -> str:
        """Render a wall buffer to a terminal string and cache it.

        Args:
            buffer: Binary wall canvas.

        Returns:
            Colored terminal string without a trailing newline.
        """
        char_grid, idx_grid = self._build_char_grid_and_idx(buffer)
        self._char_grid_cache = char_grid
        self._idx_grid_cache = idx_grid
        return self._apply_color(char_grid, idx_grid)

    def draw(self) -> None:
        """Draw the maze and solution to standard output."""
        canvas: list[bytearray] = self._build_render_buffer()
        string: str = self._render_to_string(canvas)
        sys.stdout.write(string + "\n")

    def toggle_path(self) -> bool:
        """Toggle shortest-path visibility and redraw.

        Returns:
            New path visibility state.
        """
        if not self._show_path:
            self._show_path = True
        else:
            self._show_path = False
        self.redraw()
        return self._show_path

    def change_color(self, scheme: ColorScheme) -> None:
        """Change the color scheme and redraw.

        Args:
            scheme: New color scheme.
        """
        self._color_scheme = scheme
        self.redraw()

    def redraw(self) -> None:
        """Redraw the current cached render state."""
        char_grid = self._char_grid_cache
        idx_grid = self._idx_grid_cache
        if char_grid is None or idx_grid is None:
            return self.draw()
        string: str = self._apply_color(char_grid, idx_grid)
        sys.stdout.buffer.write(string.encode("utf-8"))
        sys.stdout.write("\n")

    def on_regenerate(self, callback: Callable[[], None]) -> None:
        """Clear cached render data before regeneration.

        Args:
            callback: Regeneration callback reserved for future UI backends.
        """
        self._idx_grid_cache = None
        self._char_grid_cache = None
        pass


if __name__ == "__main__":
    maze = Maze(
        6,
        6,
        [
            bytearray([9, 1, 1, 5, 7, 0]),
            bytearray([10, 12, 2, 11, 11, 0]),
            bytearray([8, 3, 14, 10, 10, 0]),
            bytearray([10, 12, 5, 6, 10, 0]),
            bytearray([8, 5, 5, 5, 6, 0]),
            bytearray([12, 5, 5, 5, 5, 3]),
        ],
        (0, 0),
        (5, 5),
        None,
    )
    solution = Solution(
        [
            (0, 0),
            (1, 0),
            (2, 0),
            (3, 0),
            (4, 0),
            (4, 1),
            (4, 2),
            (4, 3),
            (4, 4),
        ],
        "news",
    )
    test = Visualizer(maze, solution)

    test.draw()

    test.change_color(
        ColorScheme(
            wall=ColorScheme.fg(100, 180, 255),
            path=ColorScheme.bg(30, 30, 30),
        )
    )

    test.toggle_path()

    print("=== RGB bg(wall) + bg(path) — wall bg bleeds into path ===")
    test.change_color(
        ColorScheme(
            wall=ColorScheme.fg(60, 60, 180),
            path=ColorScheme.bg(20, 20, 20),
        )
    )

    print("=== 256 color fg(wall) + bg(path) ===")
    test.change_color(
        ColorScheme(
            wall=ColorScheme.fg256(39),
            path=ColorScheme.bg256(236),
        )
    )
