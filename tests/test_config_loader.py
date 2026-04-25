from pathlib import Path

import pytest

from mazegen.ConfigLoader import ConfigLoader


def _base_config() -> dict[str, str]:
    return {
        "WIDTH": "15",
        "HEIGHT": "10",
        "ENTRY": "0,0",
        "EXIT": "14,9",
        "OUTPUT_FILE": "maze.txt",
        "PERFECT": "True",
    }


def _write_config(
    tmp_path: Path,
    *,
    overrides: dict[str, str] | None = None,
    omit: set[str] | None = None,
    extra_lines: list[str] | None = None,
) -> Path:
    values = _base_config()
    if overrides:
        values.update(overrides)
    if omit:
        for key in omit:
            values.pop(key)

    lines = [f"{key}={value}" for key, value in values.items()]
    if extra_lines:
        lines.extend(extra_lines)

    config_path = tmp_path / "config.txt"
    config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return config_path


def test_loader_accepts_comments_blank_lines_whitespace_and_seed(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "config.txt"
    config_path.write_text(
        "\n".join(
            [
                "# ignored comment",
                "",
                "WIDTH = 15\t",
                "HEIGHT=10",
                "ENTRY = 0, 0",
                "EXIT=14, 9",
                "OUTPUT_FILE = maze.txt",
                "PERFECT = True",
                "SEED = 42",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    config = ConfigLoader().load(str(config_path))

    assert config.width == 15
    assert config.height == 10
    assert config.entry == (0, 0)
    assert config.exit == (9, 14)
    assert config.output_file == "maze.txt"
    assert config.perfect is True
    assert config.seed == 42


@pytest.mark.parametrize(
    "missing_key",
    ["WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT"],
)
def test_loader_reports_each_missing_required_key(
    tmp_path: Path,
    missing_key: str,
) -> None:
    config_path = _write_config(tmp_path, omit={missing_key})

    with pytest.raises(ValueError, match=missing_key):
        ConfigLoader().load(str(config_path))


@pytest.mark.parametrize(
    ("key", "value", "message"),
    [
        ("WIDTH", "abc", "WIDTH"),
        ("WIDTH", "0", "WIDTH"),
        ("HEIGHT", "-1", "HEIGHT"),
        ("ENTRY", "0,0,0", "ENTRY"),
        ("ENTRY", "a,b", "ENTRY"),
        ("EXIT", "15,9", "inside"),
        ("PERFECT", "yes", "PERFECT"),
        ("OUTPUT_FILE", "", "value must not be empty"),
    ],
)
def test_loader_rejects_invalid_values(
    tmp_path: Path,
    key: str,
    value: str,
    message: str,
) -> None:
    config_path = _write_config(tmp_path, overrides={key: value})

    with pytest.raises(ValueError, match=message):
        ConfigLoader().load(str(config_path))


def test_loader_rejects_same_entry_and_exit(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path, overrides={"EXIT": "0,0"})

    with pytest.raises(ValueError, match="ENTRY and EXIT"):
        ConfigLoader().load(str(config_path))


def test_loader_rejects_duplicate_keys_with_key_name(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path, extra_lines=["WIDTH=20"])

    with pytest.raises(ValueError, match="Duplicate config key: WIDTH"):
        ConfigLoader().load(str(config_path))


def test_loader_rejects_unknown_keys_without_traceback(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path, extra_lines=["FOOBAR=baz"])

    with pytest.raises(ValueError, match="Unknown config key: FOOBAR"):
        ConfigLoader().load(str(config_path))
