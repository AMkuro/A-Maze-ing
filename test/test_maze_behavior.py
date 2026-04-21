from pathlib import Path

import pytest

from mazegen.ConfigLoader import AppConfig
from mazegen.MazeGenerator import Maze, MazeGenerator
from mazegen.MazeSerializer import MazeSerializer
from mazegen.MazeSolver import MazeSolver
from mazegen.Visualizer import Visualizer
from mazegen.MazeModel import Wall


def make_config(
    tmp_path: Path,
    *,
    width: int = 5,
    height: int = 5,
    perfect: bool = True,
    seed: int | None = 42,
) -> AppConfig:
    return AppConfig(
        width=width,
        height=height,
        entry=(0, 0),
        exit=(height - 1, width - 1),
        output_file=str(tmp_path / "maze.txt"),
        perfect=perfect,
        seed=seed,
        algorithm="dfs",
        display_mode="ascii",
    )


def assert_wall_bits_are_consistent(maze: Maze) -> None:
    for y in range(maze.height):
        for x in range(maze.width):
            cell = maze.grid[y][x]
            if x + 1 < maze.width:
                east_open = bool(cell & 0b0010)
                west_open = bool(maze.grid[y][x + 1] & 0b1000)
                assert east_open == west_open
            if y + 1 < maze.height:
                south_open = bool(cell & 0b0100)
                north_open = bool(maze.grid[y + 1][x] & 0b0001)
                assert south_open == north_open


@pytest.mark.parametrize(
    ("width", "height", "perfect"),
    [
        (2, 2, True),
        (5, 5, True),
        (6, 6, False),
        (20, 20, True),
    ],
)
def test_generate_solve_serialize_and_render_smoke(
    tmp_path: Path,
    width: int,
    height: int,
    perfect: bool,
) -> None:
    config = make_config(
        tmp_path,
        width=width,
        height=height,
        perfect=perfect,
    )

    maze = MazeGenerator.generate(config)
    solution = MazeSolver.solve(maze)
    serialized = MazeSerializer.serialize(maze, solution)
    rendered = Visualizer(maze, solution)._render_to_string(
        Visualizer(maze, solution)._build_render_buffer()
    )

    assert solution.path[0] == maze.entry
    assert solution.path[-1] == maze.exit
    assert solution.news
    assert len(serialized.splitlines()[0]) == width
    assert rendered.strip()
    assert_wall_bits_are_consistent(maze)


def test_seed_makes_generation_reproducible(tmp_path: Path) -> None:
    config = make_config(tmp_path, width=10, height=10, seed=123)

    first = MazeGenerator.generate(config)
    second = MazeGenerator.generate(config)

    assert [bytes(row) for row in first.grid] == [
        bytes(row) for row in second.grid
    ]


def test_solution_moves_match_path(tmp_path: Path) -> None:
    config = make_config(tmp_path, width=10, height=10, seed=7)
    maze = MazeGenerator.generate(config)
    solution = MazeSolver.solve(maze)

    assert len(solution.news) == len(solution.path) - 1
    assert set(solution.news) <= {"N", "E", "W", "S"}


def test_imperfect_maze_is_rejected_when_loop_cannot_be_created(
    tmp_path: Path,
) -> None:
    config = make_config(tmp_path, width=1, height=5, perfect=False)

    with pytest.raises(ValueError, match="single path is not a maze"):
        MazeGenerator.generate(config)


def test_42_pattern_does_not_close_entry_or_exit(tmp_path: Path) -> None:
    config = AppConfig(
        width=9,
        height=9,
        entry=(2, 1),
        exit=(6, 7),
        output_file=str(tmp_path / "maze.txt"),
        perfect=True,
        seed=42,
        algorithm="dfs",
        display_mode="ascii",
    )

    maze = MazeGenerator.generate(config)
    solution = MazeSolver.solve(maze)

    assert not maze.grid[maze.entry[0]][maze.entry[1]] & Wall.WALL_42
    assert not maze.grid[maze.exit[0]][maze.exit[1]] & Wall.WALL_42
    assert solution.path[0] == maze.entry
    assert solution.path[-1] == maze.exit
