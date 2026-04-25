from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _run_cli(
    *args: str,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "a_maze_ing.py", *args],
        cwd=PROJECT_ROOT,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )


def test_cli_rejects_missing_argument_without_traceback() -> None:
    result = _run_cli()

    assert result.returncode == 2
    assert "Usage: python3 a_maze_ing.py <config.txt>" in result.stderr
    assert "Traceback" not in result.stderr


def test_cli_rejects_extra_arguments_without_traceback() -> None:
    result = _run_cli("config.txt", "extra.txt")

    assert result.returncode == 2
    assert "Usage: python3 a_maze_ing.py <config.txt>" in result.stderr
    assert "Traceback" not in result.stderr


def test_cli_reports_missing_config_without_traceback() -> None:
    result = _run_cli("does-not-exist.txt")

    assert result.returncode == 1
    assert "Configuration file not found: does-not-exist.txt" in result.stderr
    assert "Traceback" not in result.stderr


def test_cli_generates_output_and_quits_cleanly(tmp_path: Path) -> None:
    output_path = tmp_path / "maze.txt"
    config_path = tmp_path / "config.txt"
    config_path.write_text(
        "\n".join(
            [
                "WIDTH=5",
                "HEIGHT=5",
                "ENTRY=0,0",
                "EXIT=4,4",
                f"OUTPUT_FILE={output_path}",
                "PERFECT=True",
                "SEED=42",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = _run_cli(str(config_path), input_text="4\n")

    assert result.returncode == 0
    assert output_path.exists()
    assert "Traceback" not in result.stderr
