from mazegen.MazeApp import MazeApp
import sys


def main(argv: list[str]) -> None:
    if len(argv) != 2:
        print("Usage: python3 a_maze_ing.py <config.txt>")
        return
    try:
        MazeApp().run(argv[-1])
    except Exception as e:
        print(e)
    return


if __name__ == "__main__":
    main(sys.argv)
