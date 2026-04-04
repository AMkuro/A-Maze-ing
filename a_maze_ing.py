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
    print([[str(i) for i in line] for line in maze.grid])
    visualize = Visualizer(maze, solution)
    visualize.draw()

    print("\nSolution path:")
    visualize.toggle_path()

    print("\nNews string:")
    print(solution.news)


if __name__ == "__main__":
    main()
