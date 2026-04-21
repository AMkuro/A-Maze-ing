import random
from .ConfigLoader import AppConfig
from .MazeModel import Maze, Grid, Pos, Wall

GateWay = set[tuple[int, int]]


class MazeGenerator:
    """Generate maze data for the visualizer-compatible cell grid."""

    @staticmethod
    def generate(config: "AppConfig") -> Maze:
        """Generate a maze from validated configuration.

        Args:
            config: Validated application configuration.

        Returns:
            Generated maze.

        Raises:
            ValueError: If a one-cell-wide or one-cell-high maze is requested,
                or if imperfect-maze generation cannot create a valid loop.
        """
        if config.seed is not None:
            random.seed(config.seed)

        width = config.width
        height = config.height
        entry = config.entry
        exit = config.exit

        if width == 1 or height == 1:
            raise ValueError("A maze with a single path is not a maze.")
        grid = MazeGenerator._init_grid(width, height)
        grid = MazeGenerator._embed_42_pattern(grid, {entry, exit})
        grid = MazeGenerator._carve_passages(grid)

        if not config.perfect:
            grid = MazeGenerator._make_imperfect(grid)

        return Maze(
            width=width,
            height=height,
            grid=grid,
            entry=entry,
            exit=exit,
            seed=config.seed,
        )

    @staticmethod
    def _init_grid(width: int, height: int) -> Grid:
        """Initialize all cells with every wall closed.

        Args:
            width: Maze width in cells.
            height: Maze height in cells.

        Returns:
            Grid filled with closed-wall cells.
        """
        return [
            bytearray(Wall.ALL_WALLS for _ in range(width))
            for _ in range(height)
        ]

    @staticmethod
    def _embed_42_pattern(grid: Grid, gateway: GateWay) -> Grid:
        """Embed protected ``42`` cells at the maze center.

        The 42 cells are treated as protected wall cells.

        Args:
            grid: Maze grid to mutate.
            gateway: Entry and exit positions that must remain usable.

        Returns:
            The mutated grid. The original grid is returned unchanged when the
            maze is too small or the pattern would overlap a gateway cell.
        """
        height = len(grid)
        width = len(grid[0])

        center_y = height // 2
        center_x = width // 2
        relative_gateway = {
            (pos[0] - center_y, pos[1] - center_x) for pos in gateway
        }

        pattern: set[tuple[int, int]] = {
            (-2, -3),
            (-1, -3),
            (0, -3),
            (0, -2),
            (0, -1),
            (1, -1),
            (2, -1),
            (-2, 1),
            (-2, 2),
            (-2, 3),
            (-1, 3),
            (0, 1),
            (0, 2),
            (0, 3),
            (1, 1),
            (2, 1),
            (2, 2),
            (2, 3),
        }

        if height <= 5 or width <= 7:
            print('"42" pattern has omitted by the maze size.')
            return grid

        if relative_gateway & pattern:
            print('"42" pattern has omitted by the place of entry and exit')
            return grid

        for dy, dx in pattern:
            y = center_y + dy
            x = center_x + dx

            if 0 <= y < height and 0 <= x < width:
                grid[y][x] |= Wall.WALL_42

        return grid

    @staticmethod
    def _carve_passages(grid: Grid) -> Grid:
        """Carve passages using the recursive backtracker algorithm.

        Args:
            grid: Closed-wall grid, optionally containing protected cells.

        Returns:
            Grid with carved passages.

        Raises:
            ValueError: If no non-protected starting cell exists.
        """
        height = len(grid)
        width = len(grid[0])

        start = MazeGenerator._find_start_cell(grid)
        if start is None:
            raise ValueError(
                "No valid starting cell found for maze generation."
            )

        visited = [bytearray(width) for _ in range(height)]
        stack: list[Pos] = [start]
        visited[start[0]][start[1]] = True

        directions = [
            (-1, 0, Wall.NORTH, Wall.SOUTH),
            (0, 1, Wall.EAST, Wall.WEST),
            (1, 0, Wall.SOUTH, Wall.NORTH),
            (0, -1, Wall.WEST, Wall.EAST),
        ]

        while stack:
            y, x = stack[-1]
            neighbors: list[tuple[int, int, int, int]] = []

            for dy, dx, wall, opposite_wall in directions:
                ny, nx = y + dy, x + dx
                if not (0 <= ny < height and 0 <= nx < width):
                    continue
                if visited[ny][nx]:
                    continue
                if (grid[ny][nx] & Wall.WALL_42) != 0:
                    continue

                neighbors.append((ny, nx, wall, opposite_wall))

            if neighbors:
                ny, nx, wall, opposite_wall = random.choice(neighbors)
                grid[y][x] &= ~wall
                grid[ny][nx] &= ~opposite_wall
                visited[ny][nx] = True
                stack.append((ny, nx))
            else:
                stack.pop()

        return grid

    @staticmethod
    def _find_start_cell(grid: Grid) -> Pos | None:
        """Find the first cell that is not part of the ``42`` pattern.

        Args:
            grid: Maze grid to scan.

        Returns:
            First usable cell position, or ``None`` when every cell is
            protected.
        """
        height = len(grid)
        width = len(grid[0])

        for y in range(height):
            for x in range(width):
                if not MazeGenerator._is_42_cell(grid[y][x]):
                    return (y, x)
        return None

    @staticmethod
    def _make_imperfect(grid: Grid) -> Grid:
        """Break one wall to create an imperfect maze.

        Args:
            grid: Perfect maze grid to mutate.

        Returns:
            Grid with one additional passage that creates a loop.

        Raises:
            ValueError: If every removable wall would create a 3x3 open area.
        """
        height = len(grid)
        width = len(grid[0])

        directions = [
            (-1, 0, Wall.NORTH, Wall.SOUTH),
            (0, 1, Wall.EAST, Wall.WEST),
            (1, 0, Wall.SOUTH, Wall.NORTH),
            (0, -1, Wall.WEST, Wall.EAST),
        ]

        candidates: list[tuple[int, int, int, int, int, int]] = []

        for y in range(height):
            for x in range(width):
                if MazeGenerator._is_42_cell(grid[y][x]):
                    continue

                for dy, dx, wall, opposite_wall in directions:
                    ny = y + dy
                    nx = x + dx

                    if not (0 <= ny < height and 0 <= nx < width):
                        continue
                    if MazeGenerator._is_42_cell(grid[ny][nx]):
                        continue

                    if (grid[y][x] & wall) == 0:
                        continue

                    candidates.append((y, x, ny, nx, wall, opposite_wall))

        random.shuffle(candidates)

        for y, x, ny, nx, wall, opposite_wall in candidates:
            grid[y][x] &= ~wall
            grid[ny][nx] &= ~opposite_wall

            min_y = max(0, min(y, ny) - 2)
            max_y = min(height - 3, max(y, ny))

            min_x = max(0, min(x, nx) - 2)
            max_x = min(width - 3, max(x, nx))

            bad = False

            for cy in range(min_y, max_y + 1):
                for cx in range(min_x, max_x + 1):
                    if MazeGenerator._is_open_3x3(grid, cy, cx):
                        bad = True
                        break
                if bad:
                    break

            if bad:
                grid[y][x] |= wall
                grid[ny][nx] |= opposite_wall
                continue

            return grid

        raise ValueError(
            "PERFECT = False but every removable wall creates a 3x3 open area."
        )

    @staticmethod
    def _is_open_3x3(grid: Grid, top_y: int, top_x: int) -> bool:
        """Check whether a 3x3 block is fully open internally.

        Cells belonging to the ``42`` pattern make the block invalid for this
        check.

        Args:
            grid: Maze grid to inspect.
            top_y: Top row of the 3x3 block.
            top_x: Left column of the 3x3 block.

        Returns:
            ``True`` if the block has no internal walls; otherwise ``False``.
        """

        for y in range(top_y, top_y + 3):
            for x in range(top_x, top_x + 3):
                if MazeGenerator._is_42_cell(grid[y][x]):
                    return False

        for y in range(top_y, top_y + 3):
            for x in range(top_x, top_x + 2):
                if (grid[y][x] & Wall.EAST) != 0:
                    return False
                if (grid[y][x + 1] & Wall.WEST) != 0:
                    return False

        for y in range(top_y, top_y + 2):
            for x in range(top_x, top_x + 3):
                if (grid[y][x] & Wall.SOUTH) != 0:
                    return False
                if (grid[y + 1][x] & Wall.NORTH) != 0:
                    return False

        return True

    @staticmethod
    def _is_42_cell(cell: int) -> bool:
        """Return whether a cell is marked as protected ``42`` data.

        Args:
            cell: Encoded cell value.

        Returns:
            ``True`` when the protected-cell bit is set.
        """
        return (cell & Wall.WALL_42) != 0
