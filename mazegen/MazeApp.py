from .ConfigLoader import ConfigLoader, AppConfig
from .MazeGenerator import Maze, MazeGenerator
from .MazeSolver import MazeSolver, Solution
from .Visualizer import Visualizer


class MazeApp:
    @staticmethod
    def _load_config(filepath: str) -> AppConfig:
        return ConfigLoader().load(filepath)

    @staticmethod
    def _generate(config: AppConfig) -> Maze:
        return MazeGenerator.generate(config)

    @staticmethod
    def _solve(maze: Maze) -> Solution:
        return MazeSolver.solve(maze)

    @staticmethod
    def _validate(maze: Maze) -> None:
        pass

    @staticmethod
    def _output(maze: Maze, solution: Solution) -> None:
        pass

    def _on_regenerate(self) -> None:
        pass

    def run(self, filepath: str) -> None:
        app_config: AppConfig = self._load_config(filepath)
        maze: Maze = self._generate(app_config)
        solution: Solution = self._solve(maze)
        self._validate(maze)
        self._output(maze, solution)
        Visualizer(maze, solution).draw()
