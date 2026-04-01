from typing import Callable


class Visualizer:
    def draw(self, maze: Maze, solution: Solution | None) -> None:
        pass

    def toggle_path(self) -> None:
        pass

    def change_color(self, scheme: ColorScheme) -> None:
        pass

    def on_regenerate(self, callback: Callable[[], None]) -> None:
        pass
