from .ConfigLoader import ConfigLoader, AppConfig
from .MazeGenerator import Maze, MazeGenerator
from .MazeSolver import MazeSolver, Solution
from .Visualizer import ColorScheme, Visualizer
from .MazeSerializer import MazeSerializer
from .MazeValidator import MazeValidator


class MazeApp:
    """Coordinate configuration loading, maze generation, and UI actions."""

    def __init__(self) -> None:
        """Initialize empty application state."""
        self._config: AppConfig | None = None
        self._maze: Maze | None = None
        self._solution: Solution | None = None
        self._viz: Visualizer | None = None
        self._show_path: bool = False
        self._theme_index: int = 0

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
    def _get_color_themes() -> list[ColorScheme]:
        """Return predefined terminal color themes.

        Returns:
            List of color themes used for cyclic theme switching.
            The first theme is the default visualizer color scheme.
        """
        return [
            ColorScheme(),
            ColorScheme(
                wall=ColorScheme.fg(100, 180, 255),
                path=ColorScheme.bg(20, 24, 32),
                solution=ColorScheme.bg(56, 73, 225),
                entry=ColorScheme.bg(50, 200, 80),
                exit=ColorScheme.bg(220, 70, 60),
            ),
            ColorScheme(
                wall=ColorScheme.fg(120, 220, 160),
                path=ColorScheme.bg(20, 30, 24),
                solution=ColorScheme.bg(40, 140, 90),
                entry=ColorScheme.bg(80, 210, 110),
                exit=ColorScheme.bg(220, 90, 70),
            ),
            ColorScheme(
                wall=ColorScheme.fg(255, 160, 160),
                path=ColorScheme.bg(32, 22, 22),
                solution=ColorScheme.bg(180, 70, 70),
                entry=ColorScheme.bg(70, 180, 90),
                exit=ColorScheme.bg(230, 80, 80),
            ),
            ColorScheme(
                wall=ColorScheme.fg(210, 170, 255),
                path=ColorScheme.bg(28, 22, 36),
                solution=ColorScheme.bg(120, 80, 180),
                entry=ColorScheme.bg(70, 190, 100),
                exit=ColorScheme.bg(230, 90, 90),
            ),
            ColorScheme(
                wall=ColorScheme.fg(220, 220, 220),
                path=ColorScheme.bg(30, 30, 30),
                solution=ColorScheme.bg(90, 90, 90),
                entry=ColorScheme.bg(80, 180, 100),
                exit=ColorScheme.bg(210, 80, 80),
            ),
        ]

    def _next_theme(self) -> ColorScheme:
        """Advance to the next predefined color theme.

        Returns:
            The next color theme in the cyclic theme list.
        """
        themes = self._get_color_themes()
        self._theme_index = (self._theme_index + 1) % len(themes)
        return themes[self._theme_index]

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
                self._viz.change_color(self._next_theme())
            elif cmd == "4":
                break
            else:
                if self._viz is not None:
                    self._viz.draw()
                else:
                    raise RuntimeError("Something broken, Stop the program.")
