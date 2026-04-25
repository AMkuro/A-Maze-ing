import time
from dataclasses import dataclass
import sys


@dataclass
class BenchResult:
    size: int
    gen_ms: float
    solve_ms: float
    validate_ms: float
    render_ms: float

    @property
    def total_ms(self) -> float:
        return self.gen_ms + self.solve_ms + self.validate_ms + self.render_ms


def measure_pipeline(size: int) -> BenchResult:
    """Measure the full pipeline for a single maze size.

    Runs generation, pathfinding, and ASCII rendering in sequence,
    recording the elapsed time of each stage separately.
    Args:
        size: The width and height of the square maze in cells.

    Returns:
        A BenchResult containing per-stage and total elapsed times in
        milliseconds.
    """

    from mazegen.ConfigLoader import AppConfig
    from mazegen.MazeGenerator import MazeGenerator
    from mazegen.MazeSolver import MazeSolver
    from mazegen.MazeValidator import MazeValidator
    from mazegen.Visualizer import Visualizer

    is_perfect: bool = False

    t0 = time.perf_counter()
    gen = MazeGenerator
    maze = gen.generate(
        AppConfig.model_validate(
            {
                "width": size,
                "height": size,
                "entry": (0, 0),
                "exit": (size - 1, size - 1),
                "output_file": "No_file_produce",
                "perfect": is_perfect,
            }
        )
    )
    gen_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    solution = MazeSolver.solve(maze)
    solve_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    MazeValidator().validate(maze, is_perfect)
    validate_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    Visualizer(maze, solution, True).dry_draw()
    render_ms = (time.perf_counter() - t0) * 1000

    return BenchResult(size, gen_ms, solve_ms, validate_ms, render_ms)


if __name__ == "__main__":
    args = sys.argv
    if len(args) != 2:
        print(
            "Usage: python3 measure_pipeline.py <maze_size>", file=sys.stderr
        )
        sys.exit(2)
    if not args[1].isdigit():
        print("Maze size must be integer!", file=sys.stderr)
        sys.exit(2)
    try:
        result = measure_pipeline(int(args[1]))
        print(
            f"size={result.size:4d} "
            f"gen={result.gen_ms:7.1f}ms "
            f"solve={result.solve_ms:7.1f}ms "
            f"validate={result.validate_ms:7.1f}ms "
            f"render={result.render_ms:7.1f}ms "
            f"total={result.total_ms:7.1f}ms"
        )
    except Exception as e:
        print(e)
        sys.exit(1)
    except KeyboardInterrupt:
        print("KeyboardInterrupt has detected. Program Stoped.")
        sys.exit(0)
