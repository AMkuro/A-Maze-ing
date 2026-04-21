from pathlib import Path

from mazegen.ConfigLoader import AppConfig
from mazegen.MazeGenerator import MazeGenerator
from mazegen.MazeSolver import MazeSolver
from mazegen.MazeValidator import MazeValidator


def make_config(
    tmp_path: Path,
    *,
    width: int,
    height: int,
    perfect: bool = True,
) -> AppConfig:
    return AppConfig(
        width=width,
        height=height,
        entry=(0, 0),
        exit=(height - 1, width - 1),
        output_file=str(tmp_path / "maze.txt"),
        perfect=perfect,
        seed=0,
    )


def test_embedded_42_pattern_dimensions_stay_solvable(tmp_path: Path) -> None:
    config = make_config(tmp_path, width=8, height=5)

    maze = MazeGenerator.generate(config)
    solution = MazeSolver.solve(maze)

    assert solution.path[0] == maze.entry
    assert solution.path[-1] == maze.exit


def test_maze_validator_accepts_generated_maze(tmp_path: Path) -> None:
    config = make_config(tmp_path, width=5, height=5)
    maze = MazeGenerator.generate(config)

    MazeValidator().validate(maze, perfect=True)
