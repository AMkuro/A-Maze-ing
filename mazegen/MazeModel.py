from dataclasses import dataclass

Grid = list[bytearray]
Pos = tuple[int, int]


class Wall:
    """Wall bit constants used by maze cells.

    Attributes:
        NORTH: Bit for a wall to the north of a cell.
        EAST: Bit for a wall to the east of a cell.
        SOUTH: Bit for a wall to the south of a cell.
        WEST: Bit for a wall to the west of a cell.
        WALL_42: Bit used for internal generation state, not an actual wall.
        ALL_WALLS: Bitmask with all four cardinal walls set.
    """

    NORTH = 1 << 0
    EAST = 1 << 1
    SOUTH = 1 << 2
    WEST = 1 << 3
    WALL_42 = 1 << 4
    ALL_WALLS = NORTH | EAST | SOUTH | WEST


@dataclass
class Solution:
    """Shortest path data for a maze.

    Attributes:
        path: Ordered cell positions from entry to exit.
        news: Movement string using N, E, W, and S.
    """

    path: list[Pos]
    news: str


@dataclass
class Maze:
    """Generated maze data.

    Attributes:
        width: Number of cells in each row.
        height: Number of rows.
        grid: Cell wall data encoded as bytearrays.
        entry: Entry position as ``(row, column)``.
        exit: Exit position as ``(row, column)``.
        seed: Optional random seed used for generation.
    """

    width: int
    height: int
    grid: Grid
    entry: Pos
    exit: Pos
    seed: int | None = None
