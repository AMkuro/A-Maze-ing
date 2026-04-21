from .ConfigLoader import ConfigLoader, AppConfig
from .MazeGenerator import Maze, MazeGenerator
from .MazeSolver import MazeSolver, Solution
from .Visualizer import ColorScheme, Visualizer
from .MazeSerializer import MazeSerializer
from .MazeValidator import MazeValidator
import colorsys
import random


class MazeApp:
    """Coordinate configuration loading, maze generation, and UI actions."""

    def __init__(self) -> None:
        """Initialize empty application state."""
        self._config: AppConfig | None = None
        self._maze: Maze | None = None
        self._solution: Solution | None = None
        self._viz: Visualizer | None = None
        self._show_path: bool = False

    def _load_config(self, filepath: str) -> AppConfig:
        """Load and store application configuration.

        Args:
            filepath: Path to the configuration file.

        Returns:
            Loaded configuration.

        Raises:
            FileNotFoundError: If the configuration file is missing.
            OSError: If the configuration file cannot be read.
            ValueError: If configuration parsing or validation fails.
        """
        self._config = ConfigLoader().load(filepath)
        return self._config

    def _generate(self, config: AppConfig) -> Maze:
        """Generate and store a maze.

        Args:
            config: Validated application configuration.

        Returns:
            Generated maze.

        Raises:
            ValueError: If maze generation fails.
        """
        self._maze = MazeGenerator.generate(config)
        return self._maze

    def _solve(self, maze: Maze) -> Solution:
        """Solve and store a maze solution.

        Args:
            maze: Maze to solve.

        Returns:
            Shortest path solution.

        Raises:
            ValueError: If no path exists.
        """
        self._solution = MazeSolver.solve(maze)
        return self._solution

    def _validate(self, maze: Maze, app_config: AppConfig) -> None:
        """Validate a generated maze.

        Args:
            maze: Maze to validate.
            app_config: Configuration used to generate the maze.

        Raises:
            ValueError: If maze validation fails.
        """
        perfect: bool = app_config.perfect
        try:
            MazeValidator().validate(maze, perfect)
        except Exception as e:
            raise e

    def _output(self, maze: Maze, solution: Solution) -> None:
        """Write serialized maze output to the configured file.

        Args:
            maze: Maze to serialize.
            solution: Solution to include in the output footer.

        Raises:
            RuntimeError: If configuration has not been loaded.
            OSError: If writing the output file fails.
        """
        if self._config is None:
            raise RuntimeError("Config not loaded.")

        serialized = MazeSerializer.serialize(maze, solution)
        output_path = self._config.output_path()
        output_path.write_text(serialized, encoding="utf-8")

    def _on_regenerate(self) -> None:
        """Handle the regenerate action from the interactive menu.

        Raises:
            RuntimeError: If the visualizer is unexpectedly unavailable.
        """
        app_config = self._config
        if app_config and app_config.seed is None:
            self._orchestra(app_config)
        else:
            if self._viz is not None:
                self._viz.draw()
            else:
                raise RuntimeError("Something broken, Stop the program.")

    def _orchestra(self, app_config: AppConfig) -> None:
        """Run generation, solving, validation, output, and drawing.

        Args:
            app_config: Configuration for the run.

        Raises:
            ValueError: If generation, solving, or validation fails.
            OSError: If writing the output file fails.
        """
        maze: Maze = self._generate(app_config)
        solution: Solution = self._solve(maze)
        self._validate(maze, app_config)
        self._output(maze, solution)
        self._viz = Visualizer(maze, solution, self._show_path)
        self._viz.draw()

    @staticmethod
    def get_pentadic_colors() -> list[tuple[int, int, int]]:
        """Generate five visually separated RGB colors.

        Returns:
            List of five ``(red, green, blue)`` color tuples.
        """
        colors: list[tuple[int, int, int]] = []
        start_hue: float = random.random()

        saturation = 0.8
        lightness_steps = [0.5, 0.7, 0.4, 0.8, 0.6]
        for i in range(5):
            hue = (start_hue + (i * 0.2)) % 1.0
            l_value = lightness_steps[i]
            r, g, b = colorsys.hls_to_rgb(hue, l_value, saturation)
            colors.append((int(r * 255), int(g * 255), int(b * 255)))
        return colors

    def run(self, filepath: str) -> None:
        """Run the application and interactive menu.

        Args:
            filepath: Path to the configuration file.

        Raises:
            FileNotFoundError: If the configuration file is missing.
            OSError: If reading the configuration or writing output fails.
            ValueError: If configuration, generation, solving, or validation
                fails.
            RuntimeError: If menu actions encounter invalid application state.
        """
        app_config: AppConfig = self._load_config(filepath)
        self._orchestra(app_config)

        while True:
            print("\n=== A-Maze-ing ===")
            messages: list[str] = [
                "Re-generate a new maze",
                "Show/Hide path from entry to exit",
                "Rotate maze colors",
                "Quit",
            ]
            for i, message in enumerate(messages, 1):
                print(f"{i}. {message}")
            cmd = input("Choice? (1-4): ").strip()
            if cmd == "1":
                self._on_regenerate()
            elif cmd == "2":
                if self._viz is None:
                    raise RuntimeError("Visualizer is not initialized.")
                self._show_path = self._viz.toggle_path()
            elif cmd == "3":
                if self._viz is None:
                    raise RuntimeError("Visualizer is not initialized.")
                pentadic_colors = self.get_pentadic_colors()
                self._viz.change_color(
                    ColorScheme(
                        wall=ColorScheme.fg(*pentadic_colors[0]),
                        path=ColorScheme.bg(*pentadic_colors[1]),
                        solution=ColorScheme.bg(*pentadic_colors[2]),
                        entry=ColorScheme.bg(*pentadic_colors[3]),
                        exit=ColorScheme.bg(*pentadic_colors[4]),
                    )
                )
            elif cmd == "4":
                break
