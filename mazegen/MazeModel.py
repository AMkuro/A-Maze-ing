from dataclasses import dataclass

Grid = list[bytearray]
Pos = tuple[int, int]


class Wall:
    NORTH = 1 << 0
    EAST = 1 << 1
    SOUTH = 1 << 2
    WEST = 1 << 3
    WALL_42 = 1 << 4
    ALL_WALLS = NORTH | EAST | SOUTH | WEST


@dataclass
class Maze:
    width: int
    height: int
    grid: Grid
    entry: Pos
    exit: Pos
    seed: int | None = None
