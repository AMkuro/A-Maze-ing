from collections import deque

from mazegen.ConfigLoader import AppConfig
from mazegen.MazeGenerator import MazeGenerator
from mazegen.MazeModel import Maze, Pos, Solution, Wall
from mazegen.MazeSerializer import MazeSerializer
from mazegen.MazeSolver import MazeSolver


DIRECTIONS: dict[str, tuple[int, int, int]] = {
    "N": (-1, 0, Wall.NORTH),
    "E": (0, 1, Wall.EAST),
    "S": (1, 0, Wall.SOUTH),
    "W": (0, -1, Wall.WEST),
}


def _build_output() -> tuple[Maze, Solution, str]:
    config = AppConfig(
        width=15,
        height=10,
        entry=(0, 0),
        exit=(9, 14),
        output_file="maze.txt",
        perfect=True,
        seed=42,
    )
    maze = MazeGenerator.generate(config)
    solution = MazeSolver.solve(maze)
    return maze, solution, MazeSerializer.serialize(maze, solution)


def _walk_path(maze: Maze, moves: str) -> Pos:
    y, x = maze.entry
    for move in moves:
        dy, dx, wall = DIRECTIONS[move]
        assert (maze.grid[y][x] & wall) == 0
        y += dy
        x += dx
        assert 0 <= y < maze.height
        assert 0 <= x < maze.width
    return (y, x)


def _shortest_distance(maze: Maze) -> int:
    queue: deque[tuple[Pos, int]] = deque([(maze.entry, 0)])
    seen: set[Pos] = {maze.entry}

    while queue:
        (y, x), distance = queue.popleft()
        if (y, x) == maze.exit:
            return distance
        for dy, dx, wall in DIRECTIONS.values():
            ny = y + dy
            nx = x + dx
            neighbor = (ny, nx)
            if not (0 <= ny < maze.height and 0 <= nx < maze.width):
                continue
            if neighbor in seen:
                continue
            if (maze.grid[y][x] & wall) != 0:
                continue
            seen.add(neighbor)
            queue.append((neighbor, distance + 1))

    raise AssertionError("maze has no route from entry to exit")


def test_serializer_writes_required_layout_and_lf_ending() -> None:
    maze, solution, output = _build_output()
    lines = output.splitlines()

    assert output.endswith("\n")
    assert len(lines) == maze.height + 4
    assert lines[maze.height] == ""
    assert lines[maze.height + 1] == "0,0"
    assert lines[maze.height + 2] == "14,9"
    assert lines[maze.height + 3] == solution.news
    assert set(solution.news) <= set(DIRECTIONS)

    for line in lines[:maze.height]:
        assert len(line) == maze.width
        assert set(line) <= set("0123456789ABCDEF")


def test_serialized_path_is_valid_and_shortest() -> None:
    maze, _, output = _build_output()
    path = output.splitlines()[-1]

    assert _walk_path(maze, path) == maze.exit
    assert len(path) == _shortest_distance(maze)
