from collections import deque
from typing import Deque
from .MazeModel import Maze, Wall


class MazeValidator:
    """Validate generated maze structure."""

    directions = (
        (-1, 0, Wall.NORTH),
        (1, 0, Wall.SOUTH),
        (0, -1, Wall.WEST),
        (0, 1, Wall.EAST),
    )

    @staticmethod
    def _has_wall(cell: int, wall: int) -> bool:
        """Return whether the requested wall bit is set.

        Args:
            cell: Encoded cell value.
            wall: Wall bit to test.

        Returns:
            ``True`` when the wall bit is set.
        """
        return (cell & wall) != 0

    @staticmethod
    def _check_wall_consistency(maze: "Maze") -> None:
        """Check whether adjacent cells agree on shared walls.

        Args:
            maze: Maze to validate.

        Raises:
            ValueError: If neighboring cells disagree on a shared wall.
        """
        grid: list[bytearray] = maze.grid
        width: int = maze.width
        height: int = maze.height
        has_wall = MazeValidator._has_wall

        for y in range(height):
            for x in range(width):
                cell = grid[y][x]

                if (
                    x + 1 < width
                    and (
                        has_wall(cell, Wall.EAST)
                        != has_wall(grid[y][x + 1], Wall.WEST)
                    )
                ) or (
                    y + 1 < height
                    and (
                        has_wall(cell, Wall.SOUTH)
                        != has_wall(grid[y + 1][x], Wall.NORTH)
                    )
                ):
                    raise ValueError(f"Wall Consistency Error:pos ({x},{y})")

    @staticmethod
    def _check_bounds(maze: "Maze") -> None:
        """Check whether grid size matches width and height.

        Args:
            maze: Maze to validate.

        Raises:
            ValueError: If the grid dimensions do not match the maze metadata.
        """
        grid: list[bytearray] = maze.grid
        width: int = maze.width
        height: int = maze.height
        if len(grid) != height:
            raise ValueError(
                "Check Bounds Error: grid size exceed or under of the range."
            )
        for c in range(height):
            if len(grid[c]) != width:
                raise ValueError(
                    "Check Bounds Error: grid size "
                    "exceed or under of the range."
                )

    @staticmethod
    def _check_outer_walls(maze: "Maze") -> None:
        """Check whether the outer border is fully closed.

        Args:
            maze: Maze to validate.

        Raises:
            ValueError: If any external border wall is open.
        """
        width: int = maze.width
        height: int = maze.height
        grid: list[bytearray] = maze.grid
        north_bound: bool = all(grid[0][r] & Wall.NORTH for r in range(width))
        south_bound: bool = all(grid[-1][r] & Wall.SOUTH for r in range(width))
        east_bound: bool = all(grid[c][-1] & Wall.EAST for c in range(height))
        west_bound: bool = all(grid[c][0] & Wall.WEST for c in range(height))
        if not (north_bound and south_bound and east_bound and west_bound):
            raise ValueError("There is hole at the external borders.")

    @staticmethod
    def _check_no_open_3x3(maze: "Maze") -> None:
        """Check that no fully open 3x3 area exists.

        Args:
            maze: Maze to validate.

        Raises:
            ValueError: If the maze contains a fully open 3x3 area.
        """
        grid: list[bytearray] = maze.grid
        width: int = maze.width
        height: int = maze.height

        if width < 3 or height < 3:
            return
        for y in range(height - 2):
            for x in range(width - 2):
                south_open = all(
                    not (grid[y + dy][x + dx] & Wall.SOUTH)
                    for dy in range(2)
                    for dx in range(3)
                )
                east_open = all(
                    not (grid[y + dy][x + dx] & Wall.EAST)
                    for dy in range(3)
                    for dx in range(2)
                )
                if east_open and south_open:
                    raise ValueError("There is a 3*3 open area.")

    @staticmethod
    def _check_reachability_and_loop(maze: "Maze", perfect: bool) -> None:
        """Check reachability and loop condition.

        Args:
            maze: Maze to validate.
            perfect: Whether the maze is expected to be perfect.

        Raises:
            ValueError: If cells are unreachable or loop condition is invalid.
        """
        width = maze.width
        height = maze.height
        grid = maze.grid

        cell = 0
        start: tuple[int, int] | None = None

        for y in range(height):
            for x in range(width):
                if grid[y][x] & Wall.WALL_42:
                    continue

                cell += 1
                if start is None:
                    start = (y, x)

        if start is None:
            raise ValueError("Maze has no breakable walls.")

        queue: Deque[tuple[int, int]] = deque([start])
        reached: set[tuple[int, int]] = {start}
        reachable_edge = 0

        while queue:
            y, x = queue.popleft()

            for dy, dx, wall in MazeValidator.directions:
                if grid[y][x] & wall:
                    continue

                ny = y + dy
                nx = x + dx
                if not (0 <= ny < height and 0 <= nx < width):
                    continue
                if grid[ny][nx] & Wall.WALL_42:
                    continue

                reachable_edge += 1
                neighbor = (ny, nx)
                if neighbor in reached:
                    continue

                reached.add(neighbor)
                queue.append(neighbor)

        if len(reached) != cell:
            raise ValueError("Not all cells are reachable.")

        edge = reachable_edge // 2
        if perfect and edge != cell - 1:
            raise ValueError("Maze has a loop, but should be perfect.")
        if not perfect and edge <= cell - 1:
            raise ValueError("Maze is still perfect, but should be imperfect.")

    def validate(self, maze: "Maze", perfect: bool) -> None:
        """Run all validation checks.

        Args:
            maze: Maze to validate.
            perfect: Whether the maze is expected to be perfect.

        Raises:
            ValueError: If any structural validation check fails.
        """
        self._check_bounds(maze)
        self._check_wall_consistency(maze)
        self._check_outer_walls(maze)
        self._check_no_open_3x3(maze)
        self._check_reachability_and_loop(maze, perfect)
