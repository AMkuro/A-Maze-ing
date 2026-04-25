from collections import deque

import pytest

from mazegen.ConfigLoader import AppConfig
from mazegen.MazeGenerator import MazeGenerator
from mazegen.MazeModel import Maze, Pos, Wall
from mazegen.MazeValidator import MazeValidator


DIRECTIONS: tuple[tuple[int, int, int], ...] = (
    (-1, 0, Wall.NORTH),
    (0, 1, Wall.EAST),
    (1, 0, Wall.SOUTH),
    (0, -1, Wall.WEST),
)


def _config(
    *,
    width: int = 15,
    height: int = 10,
    perfect: bool = True,
    seed: int | None = 42,
) -> AppConfig:
    return AppConfig(
        width=width,
        height=height,
        entry=(0, 0),
        exit=(height - 1, width - 1),
        output_file="maze.txt",
        perfect=perfect,
        seed=seed,
    )


def _grid_signature(maze: Maze) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(cell for cell in row) for row in maze.grid)


def _is_42_cell(cell: int) -> bool:
    return (cell & Wall.WALL_42) != 0


def _non_42_cells(maze: Maze) -> set[Pos]:
    return {
        (y, x)
        for y in range(maze.height)
        for x in range(maze.width)
        if not _is_42_cell(maze.grid[y][x])
    }


def _reachable_non_42_cells(maze: Maze) -> set[Pos]:
    start = maze.entry
    if _is_42_cell(maze.grid[start[0]][start[1]]):
        return set()

    queue: deque[Pos] = deque([start])
    seen: set[Pos] = {start}

    while queue:
        y, x = queue.popleft()
        for dy, dx, wall in DIRECTIONS:
            ny = y + dy
            nx = x + dx
            neighbor = (ny, nx)
            if not (0 <= ny < maze.height and 0 <= nx < maze.width):
                continue
            if neighbor in seen:
                continue
            if _is_42_cell(maze.grid[ny][nx]):
                continue
            if (maze.grid[y][x] & wall) != 0:
                continue
            seen.add(neighbor)
            queue.append(neighbor)

    return seen


def _open_edge_count(maze: Maze) -> int:
    edges = 0
    for y in range(maze.height):
        for x in range(maze.width):
            if _is_42_cell(maze.grid[y][x]):
                continue
            if x + 1 < maze.width:
                if not _is_42_cell(maze.grid[y][x + 1]):
                    if (maze.grid[y][x] & Wall.EAST) == 0:
                        edges += 1
            if y + 1 < maze.height:
                if not _is_42_cell(maze.grid[y + 1][x]):
                    if (maze.grid[y][x] & Wall.SOUTH) == 0:
                        edges += 1
    return edges


def test_same_seed_produces_same_maze() -> None:
    first = MazeGenerator.generate(_config(seed=42))
    second = MazeGenerator.generate(_config(seed=42))

    assert _grid_signature(first) == _grid_signature(second)


def test_different_seeds_change_the_maze() -> None:
    first = MazeGenerator.generate(_config(seed=42))
    second = MazeGenerator.generate(_config(seed=43))

    assert _grid_signature(first) != _grid_signature(second)


@pytest.mark.parametrize("perfect", [True, False])
def test_generated_maze_passes_structural_validator(perfect: bool) -> None:
    config = _config(perfect=perfect)
    maze = MazeGenerator.generate(config)

    MazeValidator().validate(maze, perfect)


def test_perfect_maze_is_connected_tree_excluding_42_cells() -> None:
    maze = MazeGenerator.generate(_config(perfect=True))
    non_42 = _non_42_cells(maze)

    assert _reachable_non_42_cells(maze) == non_42
    assert _open_edge_count(maze) == len(non_42) - 1


def test_imperfect_maze_keeps_connectivity_and_adds_a_loop() -> None:
    maze = MazeGenerator.generate(_config(perfect=False))
    non_42 = _non_42_cells(maze)

    assert _reachable_non_42_cells(maze) == non_42
    assert _open_edge_count(maze) >= len(non_42)


def test_42_pattern_cells_are_fully_closed_when_size_allows() -> None:
    maze = MazeGenerator.generate(_config(width=15, height=10))
    pattern_cells = [
        cell
        for row in maze.grid
        for cell in row
        if _is_42_cell(cell)
    ]

    assert len(pattern_cells) == 18
    assert all(
        (cell & Wall.ALL_WALLS) == Wall.ALL_WALLS
        for cell in pattern_cells
    )


def test_small_maze_omits_42_pattern_with_console_message(
    capsys: pytest.CaptureFixture[str],
) -> None:
    maze = MazeGenerator.generate(_config(width=3, height=3))
    output = capsys.readouterr()

    assert '"42" pattern has omitted' in output.out
    assert all(
        not _is_42_cell(cell)
        for row in maze.grid
        for cell in row
    )


@pytest.mark.xfail(
    reason=(
        "Known issue #36: MazeValidator does not reject "
        "disconnected mazes."
    ),
    strict=True,
)
def test_validator_rejects_disconnected_non_42_cells() -> None:
    maze = Maze(
        width=2,
        height=2,
        grid=[
            bytearray([Wall.ALL_WALLS, Wall.ALL_WALLS]),
            bytearray([Wall.ALL_WALLS, Wall.ALL_WALLS]),
        ],
        entry=(0, 0),
        exit=(1, 1),
    )

    with pytest.raises(ValueError, match="connect|isolated|solution"):
        MazeValidator().validate(maze, perfect=True)


@pytest.mark.xfail(
    reason=(
        "Known issue #36: MazeValidator does not reject cycles "
        "in perfect mode."
    ),
    strict=True,
)
def test_validator_rejects_cycles_when_perfect_is_required() -> None:
    maze = Maze(
        width=2,
        height=2,
        grid=[
            bytearray([Wall.NORTH | Wall.WEST, Wall.NORTH | Wall.EAST]),
            bytearray([Wall.SOUTH | Wall.WEST, Wall.SOUTH | Wall.EAST]),
        ],
        entry=(0, 0),
        exit=(1, 1),
    )

    with pytest.raises(ValueError, match="perfect|cycle|path"):
        MazeValidator().validate(maze, perfect=True)
