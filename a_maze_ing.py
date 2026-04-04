from mazegen.MazeGenerator import MazeGenerator
from mazegen.MazeSolver import MazeSolver
from mazegen.Visualizer import Visualizer
from mazegen.ConfigLoader import ConfigLoader


def main():
    config = ConfigLoader()
    config = config.load(filepath="config.txt")
    maze = MazeGenerator.generate(config)
    solution = MazeSolver.solve(maze)

    print("Maze:")
    visualize = Visualizer(maze, solution)
    visualize.draw()

    print("\nSolution path:")
    for pos in solution.path:
        print(pos)
    visualize.toggle_path()
    visualize.redraw()

    print("\nNews string:")
    print(solution.news)


if __name__ == "__main__":
    main()
