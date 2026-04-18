from .MazeGenerator import Maze

NORTH = 1 << 0
EAST = 1 << 1
SOUTH = 1 << 2
WEST = 1 << 3


class MazeValidator:
    @staticmethod
    def _check_wall_consistency(maze: "Maze") -> None:
        """Check whether adjacent cells agree on shared walls."""
        grid: list[list[int]] = maze.grid
        width: int = maze.width
        height: int = maze.height
        for r in range(width):
            for c in range(height):
                east_to_west: bool = True
                south_to_north: bool = True
                west_to_east: bool = True
                north_to_south: bool = True
                if r + 1 < width:
                    east_to_west = grid[c][r] & EAST == grid[c][r + 1] & WEST
                if c + 1 < height:
                    south_to_north = (
                        grid[c][r] & SOUTH == grid[c + 1][r] & NORTH
                    )
                if r - 1 >= 0:
                    west_to_east = grid[c][r] & WEST == grid[c][r - 1] & EAST
                if c - 1 >= 0:
                    north_to_south = (
                        grid[c][r] & NORTH == grid[c - 1][r] & SOUTH
                    )
                if (
                    not east_to_west
                    or not south_to_north
                    or not west_to_east
                    or not north_to_south
                ):
                    raise ValueError(f"Wall Consistency Error:pos ({c},{r})")

    @staticmethod
    def _check_bounds(maze: "Maze") -> None:
        """Check whether grid size matches width and height."""
        grid: list[list[int]] = maze.grid
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
        """Check whether the outer border is fully closed."""
        width: int = maze.width
        height: int = maze.height
        grid: list[list[int]] = maze.grid
        north_bound: bool = all(grid[0][r] & NORTH for r in range(width))
        south_bound: bool = all(grid[-1][r] & SOUTH for r in range(width))
        east_bound: bool = all(grid[c][-1] & EAST for c in range(height))
        west_bound: bool = all(grid[c][0] & WEST for c in range(height))
        if not (north_bound and south_bound and east_bound and west_bound):
            raise ValueError("There is hole at the external borders.")

    @staticmethod
    def _check_no_open_3x3(maze: "Maze") -> None:
        """Check that no fully open 3x3 area exists."""
        grid: list[list[int]] = maze.grid
        width: int = maze.width
        height: int = maze.height

        if width < 3 or height < 3:
            return
        for y in range(height - 2):
            for x in range(width - 2):
                south_open = all(
                    not (grid[y + dy][x + dx] & SOUTH)
                    for dy in range(2)
                    for dx in range(3)
                )
                east_open = all(
                    not (grid[y + dy][x + dx] & EAST)
                    for dy in range(3)
                    for dx in range(2)
                )
                if east_open and south_open:
                    raise ValueError("There is a 3*3 open area.")

    @staticmethod
    def _check_imperfect(maze: "Maze") -> None:
        """Check that the maze contains at least one loop."""
        width = maze.width
        height = maze.height
        grid = maze.grid

        cell = width * height
        edge = 0

        for y in range(height):
            for x in range(width):
                if x + 1 < width and (grid[y][x] & EAST) == 0:
                    edge += 1
                if y + 1 < height and (grid[y][x] & SOUTH) == 0:
                    edge += 1

        if edge <= cell - 1:
            raise ValueError("Maze is still perfect, but should be imperfect.")

    def validate(self, maze: "Maze", perfect: bool) -> None:
        """Run all validation checks."""
        self._check_bounds(maze)
        self._check_wall_consistency(maze)
        self._check_outer_walls(maze)
        self._check_no_open_3x3(maze)

        if not perfect:
            self._check_imperfect(maze)
