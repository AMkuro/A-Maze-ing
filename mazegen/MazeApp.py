from .ConfigLoader import ConfigLoader, AppConfig
from .MazeGenerator import Maze, MazeGenerator
from .MazeSolver import MazeSolver, Solution
from .Visualizer import ColorScheme, Visualizer
import colorsys
import random


class MazeApp:
    def __init__(self) -> None:
        self._config: AppConfig | None = None
        self._maze: Maze | None = None
        self._solution: Solution | None = None
        self._viz: Visualizer | None = None
        self._show_path: bool = False

    def _load_config(self, filepath: str) -> AppConfig:
        self._config = ConfigLoader().load(filepath)
        return self._config

    def _generate(self, config: AppConfig) -> Maze:
        self._maze = MazeGenerator.generate(config)
        return self._maze

    def _solve(self, maze: Maze) -> Solution:
        self._solution = MazeSolver.solve(maze)
        return self._solution

    @staticmethod
    def _validate(maze: Maze) -> None:
        pass

    @staticmethod
    def _output(maze: Maze, solution: Solution) -> None:
        pass

    def _on_regenerate(self) -> None:
        app_config = self._config
        if app_config and app_config.seed is None:
            self._orchestra(app_config)
        else:
            if self._viz is not None:
                self._viz.draw()
            else:
                raise RuntimeError("Something broken, Stop the program.")

    def _orchestra(self, app_config: AppConfig) -> None:
        maze: Maze = self._generate(app_config)
        solution: Solution = self._solve(maze)
        self._validate(maze)
        self._output(maze, solution)
        self._viz = Visualizer(maze, solution, self._show_path)
        self._viz.draw()

    @staticmethod
    def get_pentadic_colors() -> list[tuple[int, int, int]]:
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
                self._show_path = self._viz.toggle_path()
            elif cmd == "3":
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
