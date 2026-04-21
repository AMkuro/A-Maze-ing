from pathlib import Path

import pytest

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


@pytest.mark.parametrize(
    ("line", "message"),
    [
        (
            "THIS_IS_NOT_KEY_VALUE",
            "Invalid config line 7: expected KEY=VALUE.",
        ),
        ("=value", "Invalid config line 7: key must not be empty."),
        ("WIDTH=", "Invalid config line 7: value must not be empty."),
        ("UNKNOWN=1", "Unknown config key: UNKNOWN."),
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

    with pytest.raises(ValueError, match="Duplicate config key: WIDTH."):
        ConfigLoader().load(str(config_path))


@pytest.mark.parametrize(
    ("replacement", "message"),
    [
        ("WIDTH=0", "WIDTH: Input should be greater than 0"),
        ("WIDTH=abc", "WIDTH: Input should be a valid integer"),
        ("ENTRY=0", "ENTRY: must be coordinates in x,y format."),
        ("EXIT=0,0", "ENTRY and EXIT must be different."),
        ("PERFECT=maybe", "PERFECT: Input should be a valid boolean"),
    ],
)
def test_load_reports_validation_errors(
    tmp_path: Path,
    replacement: str,
    message: str,
) -> None:
    lines = valid_config(tmp_path / "maze.txt").splitlines()
    key = replacement.split("=", 1)[0]
    replaced = False
    output_lines: list[str] = []
    for line in lines:
        if line.startswith(f"{key}="):
            output_lines.append(replacement)
            replaced = True
        else:
            output_lines.append(line)
    if not replaced:
        output_lines.append(replacement)
    body = "\n".join(output_lines)
    config_path = write_config(tmp_path, body)

    with pytest.raises(ValueError, match=message):
        ConfigLoader().load(str(config_path))


def test_load_reports_missing_config_file_clearly(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.txt"

    with pytest.raises(
        FileNotFoundError,
        match=f"Configuration file not found: {missing_path}",
    ):
        ConfigLoader().load(str(missing_path))
