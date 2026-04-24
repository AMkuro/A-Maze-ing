import unittest

from ConfigLoader import AppConfig


class AppConfigOutputFileTest(unittest.TestCase):
    def test_output_file_is_trimmed_when_constructed_directly(self) -> None:
        config = AppConfig(
            width=3,
            height=3,
            entry=(0, 0),
            exit=(2, 2),
            output_file="  maze.txt  ",
            perfect=True,
        )

        self.assertEqual(config.output_file, "maze.txt")
        self.assertEqual(str(config.output_path()), "maze.txt")


if __name__ == "__main__":
    unittest.main()
