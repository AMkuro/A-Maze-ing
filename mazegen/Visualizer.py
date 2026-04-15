from dataclasses import dataclass
from .MazeGenerator import Maze
from .MazeSolver import Solution
import sys
from typing import Callable

NORTH = 1 << 0
EAST = 1 << 1
SOUTH = 1 << 2
WEST = 1 << 3

RESET = "\033[0m"


@dataclass
class ColorScheme:
    wall: str = ""
    path: str = ""
    solution: str = "\033[48;2;56;73;225m"
    entry: str = "\033[48;2;50;200;80m"
    exit: str = "\033[48;2;220;70;60m"

    @staticmethod
    def fg(r: int, g: int, b: int) -> str:
        return f"\033[38;2;{r};{g};{b}m"

    @staticmethod
    def bg(r: int, g: int, b: int) -> str:
        return f"\033[48;2;{r};{g};{b}m"

    @staticmethod
    def fg256(n: int) -> str:
        return f"\033[38;5;{n}m"

    @staticmethod
    def bg256(n: int) -> str:
        return f"\033[48;5;{n}m"


class Visualizer:
    def __init__(
        self, maze: Maze, solution: Solution, show_path: bool = False
    ) -> None:
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
        if self._render_ratio_cache is None:
            src_rows = 2 * self._maze.height + 1
            src_cols = 2 * self._maze.width + 1
            row_pairs = self._make_src_pairs(
                src_rows, even_repeat=1, odd_repeat=2
            )
            col_pairs = self._make_src_pairs(
                src_cols, even_repeat=1, odd_repeat=5
            )
            self._render_ratio_cache = (row_pairs, col_pairs)

        return self._render_ratio_cache

    def _build_render_buffer(self) -> list[bytearray]:
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
                if cell & NORTH:
                    row_top[left:left + 3] = set_of_wall

                # West Wall
                if cell & WEST:
                    row_top[left] = 1
                    row_center[left] = 1
                    row_bottom[left] = 1

        # The last row for setting South Wall
        last_grid_row = grid[h - 1]
        last_canvas_row = canvas[-1]
        for c in range(w):
            if last_grid_row[c] & SOUTH:
                left = 2 * c
                last_canvas_row[left:left + 3] = set_of_wall

        # The last column for setting East Wall
        right_col = -1
        for r in range(h):
            if grid[r][w - 1] & EAST:
                top = 2 * r
                center_r = top + 1
                bottom = top + 2
                canvas[top][right_col] = 1
                canvas[center_r][right_col] = 1
                canvas[bottom][right_col] = 1
        return canvas

    def _build_char_grid_and_idx(
        self, buffer: list[bytearray]
    ) -> tuple[list[list[str]], list[bytearray]]:
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
        wall_pre = self._color_scheme.wall
        path_pre = self._color_scheme.path
        entry_pre = self._color_scheme.entry
        exit_pre = self._color_scheme.exit
        solution_pre = self._color_scheme.solution
        row_pairs, col_pairs = self._get_render_pairs()

        rows = len(char_grid)
        cols = len(char_grid[0]) if rows > 0 else 0

        highlight: list[list[str]] = [[""] * cols for _ in range(rows)]

        for (mr, mc), color in [
            (pos, solution_pre) for pos in self._solution.path
        ] + [
            (self._maze.entry, entry_pre),
            (self._maze.exit, exit_pre),
        ]:
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
                    r == last_row and (v & 0b1100) == 0b1100
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
        char_grid, idx_grid = self._build_char_grid_and_idx(buffer)
        self._char_grid_cache = char_grid
        self._idx_grid_cache = idx_grid
        return self._apply_color(char_grid, idx_grid)

    def draw(self) -> None:
        """Maze と Solution を GUI に描画する"""
        canvas: list[bytearray] = self._build_render_buffer()
        string: str = self._render_to_string(canvas)
        sys.stdout.write(string + "\n")

    def toggle_path(self) -> bool:
        """最短経路の表示・非表示を切り替える"""
        if not self._show_path:
            self._show_path = True
        else:
            self._show_path = False
        self.redraw()
        return self._show_path

    def change_color(self, scheme: ColorScheme) -> None:
        """壁・通路・経路の配色を指定のカラースキームに変更して再描画する"""
        self._color_scheme = scheme
        self.redraw()

    def redraw(self) -> None:
        char_grid = self._char_grid_cache
        idx_grid = self._idx_grid_cache
        if char_grid is None or idx_grid is None:
            return self.draw()
        string: str = self._apply_color(char_grid, idx_grid)
        sys.stdout.buffer.write(string.encode("utf-8"))
        sys.stdout.write("\n")

    def on_regenerate(self, callback: Callable[[], None]) -> None:
        """再生成ボタン押下時に呼ばれるコールバックを登録する"""
        self._idx_grid_cache = None
        self._char_grid_cache = None
        pass


if __name__ == "__main__":
    maze = Maze(
        6,
        6,
        [
            [9, 1, 1, 5, 7, 0],
            [10, 12, 2, 11, 11, 0],
            [8, 3, 14, 10, 10, 0],
            [10, 12, 5, 6, 10, 0],
            [8, 5, 5, 5, 6, 0],
            [12, 5, 5, 5, 5, 3],
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
