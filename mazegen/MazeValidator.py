from dataclasses import dataclass

NORTH = 1 << 0
EAST = 1 << 1
SOUTH = 1 << 2
WEST = 1 << 3


class MazeValidator:
    @staticmethod
    def _check_wall_consistency(maze: "Maze") -> None:
        grid: list[list[int]] = maze.grid
        width: int = maze.width
        height: int = maze.height
        # 植木算
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
    def _check_connectivity(maze: "Maze") -> None:
        pass

    @staticmethod
    def _check_isolated_cells(maze: "Maze") -> None:
        pass

    @staticmethod
    def _check_no_open_3x3(maze: "Maze") -> None:
        pass

    @staticmethod
    def _check_perfect(maze: "Maze") -> None:
        pass

    def validate(self, maze: "Maze") -> None:
        pass


# 仮オキ


@dataclass
class Maze:
    width: int
    height: int
    grid: list[list[int]]
    entry: tuple[int, int]
    exit: tuple[int, int]
    seed: int | None
