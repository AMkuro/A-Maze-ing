from dataclasses import dataclass
import sys
from typing import Callable
import numpy as np

NORTH = 1 << 0
EAST = 1 << 1
SOUTH = 1 << 2
WEST = 1 << 3

RESET = "\033[0m"


@dataclass
class ColorScheme:
    wall: str = ""
    path: str = ""
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
    def __init__(self, maze: "Maze", solution: "Solution") -> None:
        self._maze = maze
        self._solution = solution
        self._show_path: bool = False
        self._color_scheme: ColorScheme = ColorScheme()

    def _build_render_buffer(self) -> np.ndarray:
        maze = self._maze
        w, h = maze.width, maze.height
        grid = np.array(maze.grid, dtype=np.uint8)
        canvas = np.ones((2 * h + 1, 2 * w + 1), dtype=bool)

        canvas[1::2, 1::2] = False
        canvas[0:2 * h:2, 1::2] = (grid & NORTH) != 0
        canvas[2 * h, 1::2] = (grid[-1] & SOUTH) != 0
        canvas[1::2, 0:2 * w:2] = (grid & WEST) != 0
        canvas[1::2, 2 * w] = (grid[:, -1] & EAST) != 0

        padded = np.pad(canvas, 1, constant_values=False)
        er = np.arange(0, 2 * h + 1, 2)
        ec = np.arange(0, 2 * w + 1, 2)
        per, pec = er + 1, ec + 1
        canvas[np.ix_(er, ec)] = (
            padded[np.ix_(per - 1, pec)]
            | padded[np.ix_(per + 1, pec)]
            | padded[np.ix_(per, pec - 1)]
            | padded[np.ix_(per, pec + 1)]
        )
        return canvas

    def _render_to_string(self, buffer: np.ndarray) -> str:
        LOOKUP = np.array(
            [
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
            ],
            dtype="<U1",
        )

        rows, cols = buffer.shape
        row_idx = np.array(
            [r for r in range(rows) for _ in range(1 if r % 2 == 0 else 2)]
        )
        col_idx = np.array(
            [c for c in range(cols) for _ in range(1 if c % 2 == 0 else 5)]
        )
        buf = buffer[np.ix_(row_idx, col_idx)].astype(np.uint8)
        buf = np.pad(
            buf,
            ((0, buf.shape[0] % 2), (0, buf.shape[1] % 2)),
            constant_values=0,
        )
        tl = buf[0::2, 0::2]
        tr = buf[0::2, 1::2]
        bl = buf[1::2, 0::2]
        br = buf[1::2, 1::2]
        idx = (tl << 3) | (tr << 2) | (bl << 1) | br

        char_grid = LOOKUP[idx]

        return self._apply_color(char_grid, idx, row_idx, col_idx)

    def _apply_color(
        self,
        char_grid: np.ndarray,
        idx: np.ndarray,
        row_idx,
        col_idx,
    ) -> str:
        wall_pre = self._color_scheme.wall
        path_pre = self._color_scheme.path
        entry_pre = self._color_scheme.entry
        exit_pre = self._color_scheme.exit
        highlight = np.full(char_grid.shape, "", dtype=object)

        for (mr, mc), color in [
            (self._maze.entry, entry_pre),
            (self._maze.exit, exit_pre),
        ]:
            if not color:
                continue
            out_rows = np.unique(np.where(row_idx == 2 * mr + 1)[0] // 2)
            out_cols = np.unique(np.where(col_idx == 2 * mc + 1)[0] // 2)
            for r in out_rows:
                for c in out_cols:
                    highlight[r, c] = color
        last_row = char_grid.shape[0] - 1
        last_col = char_grid.shape[1] - 1
        lines = []
        for r in range(char_grid.shape[0]):
            row = []
            for c in range(char_grid.shape[1]):
                v = int(idx[r, c])
                hl = highlight[r, c]
                suppress_bg = c == last_col or (
                    r == last_row and (v & 0b1100 == 0b1100)
                )
                bg = "" if suppress_bg else (hl or path_pre)
                if v == 0:
                    pre = bg
                elif v == 15:
                    pre = (hl or "") + wall_pre if hl else wall_pre
                else:
                    pre = bg + wall_pre
                ch = char_grid[r, c]
                row.append(f"{pre}{ch}{RESET}" if pre else ch)
            lines.append("".join(row))
        return "\n".join(lines)

    def draw(self) -> None:
        """Maze と Solution を GUI に描画する"""
        canvas: np.ndarray = self._build_render_buffer()
        string: str = self._render_to_string(canvas)
        sys.stdout.write(string + "\n")

    def toggle_path(self) -> None:
        """最短経路の表示・非表示を切り替える"""
        pass

    def change_color(self, scheme: ColorScheme) -> None:
        """壁・通路・経路の配色を指定のカラースキームに変更して再描画する"""
        self._color_scheme = scheme
        self.draw()

    def on_regenerate(self, callback: Callable[[], None]) -> None:
        """再生成ボタン押下時に呼ばれるコールバックを登録する"""
        pass


if __name__ == "__main__":

    @dataclass
    class Maze:
        """Maze data structure passed to the visualizer."""

        width: int
        height: int
        grid: list[list[int]]
        entry: tuple[int, int]
        exit: tuple[int, int]
        seed: int | None

    class Solution:
        pass

    maze = Maze(
        7,
        7,
        [
            [0, 0, 4, 0, 8, 0, 12],
            [0, 0, 0, 0, 0, 0, 0],
            [1, 0, 5, 0, 9, 0, 13],
            [0, 0, 0, 0, 0, 0, 0],
            [2, 0, 6, 0, 10, 0, 14],
            [0, 0, 0, 0, 0, 0, 0],
            [3, 0, 7, 0, 11, 0, 15],
        ],
        (0, 0),
        (6, 6),
        None,
    )
    solution = Solution()
    test = Visualizer(maze, solution)

    test.draw()

    # test.change_color(
    #     ColorScheme(
    #         wall=ColorScheme.fg(100, 180, 255),
    #         path=ColorScheme.bg(30, 30, 30),
    #     )
    # )
    #
    # print("=== RGB bg(wall) + bg(path) — wall bg bleeds into path ===")
    # test.change_color(
    #     ColorScheme(
    #         wall=ColorScheme.fg(60, 60, 180),
    #         path=ColorScheme.bg(20, 20, 20),
    #     )
    # )
    #
    # print("=== 256 color fg(wall) + bg(path) ===")
    # test.change_color(
    #     ColorScheme(
    #         wall=ColorScheme.fg256(39),
    #         path=ColorScheme.bg256(236),
    #     )
    # )
