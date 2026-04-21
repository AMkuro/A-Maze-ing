from mazegen.MazeApp import MazeApp
import sys


def main(argv: list[str]) -> int:
    """Run the A-Maze-ing CLI.

    Args:
        argv: Command-line arguments including the program name.

    Returns:
        Process exit code. Returns 0 on success, 1 for runtime/configuration
        errors, and 2 for invalid command-line usage.
    """
    if len(argv) != 2:
        print("Usage: python3 a_maze_ing.py <config.txt>", file=sys.stderr)
        return 2
    try:
        MazeApp().run(argv[-1])
    except Exception as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
