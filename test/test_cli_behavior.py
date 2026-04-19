import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP = PROJECT_ROOT / "a_maze_ing.py"
OUTPUT_VALIDATOR = PROJECT_ROOT / "output_validator.py"


def write_config(tmp_path: Path, body: str) -> Path:
    config_path = tmp_path / "config.txt"
    config_path.write_text(body, encoding="utf-8")
    return config_path


def valid_config(tmp_path: Path, *, width: int = 5, height: int = 5) -> str:
    return "\n".join(
        [
            f"WIDTH={width}",
            f"HEIGHT={height}",
            "ENTRY=0,0",
            f"EXIT={width - 1},{height - 1}",
            f"OUTPUT_FILE={tmp_path / 'maze.txt'}",
            "PERFECT=True",
        ]
    )


def run_app(
    config_path: Path,
    user_input: str = "4\n",
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(APP), str(config_path)],
        input=user_input,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=config_path.parent,
        timeout=10,
        check=False,
    )


def test_cli_valid_config_quits_without_traceback(tmp_path: Path) -> None:
    config_path = write_config(tmp_path, valid_config(tmp_path))

    result = run_app(config_path)

    assert result.returncode == 0
    assert "Traceback" not in result.stdout
    assert "Traceback" not in result.stderr
    assert (tmp_path / "maze.txt").exists()


def test_cli_invalid_menu_inputs_do_not_crash(tmp_path: Path) -> None:
    config_path = write_config(tmp_path, valid_config(tmp_path))

    result = run_app(config_path, "x\n5\n\n4\n")

    assert result.returncode == 0
    assert "Traceback" not in result.stdout
    assert "Traceback" not in result.stderr


def test_output_validator_accepts_generated_output(tmp_path: Path) -> None:
    config_path = write_config(
        tmp_path,
        valid_config(tmp_path, width=20, height=20),
    )

    app_result = run_app(config_path)
    validator_result = subprocess.run(
        [sys.executable, str(OUTPUT_VALIDATOR), str(tmp_path / "maze.txt")],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=tmp_path,
        timeout=10,
        check=False,
    )

    assert app_result.returncode == 0
    assert validator_result.returncode == 0
    assert validator_result.stdout == ""
    assert validator_result.stderr == ""


@pytest.mark.xfail(
    reason="CLI currently catches errors, prints them to stdout, and exits 0.",
    strict=True,
)
def test_cli_invalid_config_reports_failure_on_stderr(tmp_path: Path) -> None:
    config_path = write_config(
        tmp_path,
        valid_config(tmp_path).replace("WIDTH=5", "WIDTH=0"),
    )

    result = run_app(config_path)

    assert result.returncode != 0
    assert "width" in result.stderr.lower()
    assert "greater than 0" in result.stderr
    assert "Traceback" not in result.stdout
    assert "Traceback" not in result.stderr
