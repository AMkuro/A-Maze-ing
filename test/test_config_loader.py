from pathlib import Path

import pytest
from pydantic import ValidationError

from mazegen.ConfigLoader import ConfigLoader


def write_config(tmp_path: Path, body: str) -> Path:
    config_path = tmp_path / "config.txt"
    config_path.write_text(body, encoding="utf-8")
    return config_path


def valid_config(output_file: Path) -> str:
    return "\n".join(
        [
            "WIDTH=5",
            "HEIGHT=4",
            "ENTRY=0,0",
            "EXIT=4,3",
            f"OUTPUT_FILE={output_file}",
            "PERFECT=True",
        ]
    )


def test_load_valid_config_parses_fields(tmp_path: Path) -> None:
    config_path = write_config(tmp_path, valid_config(tmp_path / "maze.txt"))

    config = ConfigLoader().load(str(config_path))

    assert config.width == 5
    assert config.height == 4
    assert config.entry == (0, 0)
    assert config.exit == (3, 4)
    assert config.output_path() == tmp_path / "maze.txt"
    assert config.perfect is True
    assert config.algorithm == "dfs"
    assert config.display_mode == "ascii"


@pytest.mark.parametrize(
    ("line", "message"),
    [
        ("THIS_IS_NOT_KEY_VALUE", "Parse format is incorrect"),
        ("=value", "Config key must not be empty"),
        ("UNKNOWN=1", "Unknown config key: UNKNOWN"),
    ],
)
def test_load_rejects_malformed_lines(
    tmp_path: Path,
    line: str,
    message: str,
) -> None:
    config_path = write_config(
        tmp_path,
        valid_config(tmp_path / "maze.txt") + f"\n{line}\n",
    )

    with pytest.raises(ValueError, match=message):
        ConfigLoader().load(str(config_path))


def test_load_rejects_duplicate_keys(tmp_path: Path) -> None:
    config_path = write_config(
        tmp_path,
        valid_config(tmp_path / "maze.txt") + "\nWIDTH=6\n",
    )

    with pytest.raises(ValueError, match="WIDTH is duplicate"):
        ConfigLoader().load(str(config_path))


@pytest.mark.parametrize(
    ("replacement", "message"),
    [
        ("WIDTH=0", "greater than 0"),
        ("WIDTH=abc", "valid integer"),
        ("ENTRY=0", "point must be x,y"),
        ("EXIT=0,0", "entry and exit must be different"),
        ("PERFECT=maybe", "valid boolean"),
        ("ALGORITHM=astar", "prim.*kruskal.*dfs"),
        ("DISPLAY_MODE=html", "ascii.*mlx"),
    ],
)
def test_load_reports_validation_errors(
    tmp_path: Path,
    replacement: str,
    message: str,
) -> None:
    lines = valid_config(tmp_path / "maze.txt").splitlines()
    key = replacement.split("=", 1)[0]
    body = "\n".join(
        replacement if line.startswith(f"{key}=") else line for line in lines
    )
    config_path = write_config(tmp_path, body)

    with pytest.raises(ValidationError, match=message):
        ConfigLoader().load(str(config_path))
