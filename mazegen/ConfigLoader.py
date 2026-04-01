from pathlib import Path
from typing_extensions import Self
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)
from typing import ClassVar, Literal


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    width: int = Field(gt=0)
    height: int = Field(gt=0)
    entry: tuple[int, int]
    exit: tuple[int, int]
    output_file: str
    perfect: bool
    seed: int | None = None
    algorithm: Literal["prim", "kruskal", "dfs"] = "dfs"
    display_mode: Literal["ascii", "mlx"] = "ascii"

    @field_validator("entry", "exit", mode="before")
    @classmethod
    def parse_point(cls, value: object) -> object:
        if isinstance(value, str):
            parts: list[str] = value.split(",")
            if len(parts) != 2:
                raise ValueError("point must be x,y")
            x_str, y_str = parts
            return (int(x_str.strip()), int(y_str.strip()))
        return value

    _forbidden_file_chars: ClassVar[frozenset[str]] = frozenset(
        '\x00\n\r<>|*?"'
    )

    @field_validator("output_file")
    @classmethod
    def validate_output_file(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("output_file must not be empty")
        bad: set[str] = set(value) & AppConfig._forbidden_file_chars
        if bad:
            raise ValueError(
                f"output_file contains invalid characters: {sorted(bad)!r}"
            )
        return value

    @model_validator(mode="after")
    def validate_positions(self) -> Self:
        for name, (x, y) in (("entry", self.entry), ("exit", self.exit)):
            if not (0 <= x < self.width and 0 <= y < self.height):
                raise ValueError(f"{name} is out of bounds")
        if self.entry == self.exit:
            raise ValueError("entry and exit must be different")
        return self

    def output_path(self) -> Path:
        return Path(self.output_file)


class ConfigLoader:
    key_map: dict[str, str] = {
        "WIDTH": "width",
        "HEIGHT": "height",
        "ENTRY": "entry",
        "EXIT": "exit",
        "OUTPUT_FILE": "output_file",
        "PERFECT": "perfect",
        "SEED": "seed",
        "ALGORITHM": "algorithm",
        "DISPLAY_MODE": "display_mode",
    }

    def load(self, filepath: str) -> AppConfig:
        """ファイル読み込みからバリデーションまで一連の処理を実行しAppConfigを返す"""
        clean_lines: list[str] = self._read_lines(filepath)
        parsed_lines: list[tuple[str, str]] = []
        for line in clean_lines:
            pair = self._parse_line(line)
            parsed_lines.append(pair)
        self._check_duplicate_keys(parsed_lines)
        return self._convert_and_validate(parsed_lines)

    def _read_lines(self, filepath: str) -> list[str]:
        """ファイルを開き,コメント/空行を除いた行リストを返す"""
        processed_line: list[str] = []
        try:
            with open(filepath, encoding="utf-8") as f:
                for line in f:
                    line = line.rstrip("\n").strip()
                    if not line.startswith("#") and line:
                        processed_line.append(line)
        except Exception as e:  # TODO:Narrow the Exception
            raise e
        return processed_line

    @staticmethod
    def _parse_line(line: str) -> tuple[str, str]:
        """key=value形式の一行をパースしてタプルで返す"""
        key_value: list[str] = line.split("=", 1)
        if len(key_value) != 2:
            raise ValueError("Parse format is incorrect.")
        key, value = (part.strip() for part in key_value)
        if not key:
            raise ValueError("Config key must not be empty.")
        return (key, value)

    @staticmethod
    def _check_duplicate_keys(pairs: list[tuple[str, str]]) -> None:
        """キーの重複があれば、例外を送出する"""
        seen: set[str] = set()
        for key, _ in pairs:
            if key in seen:
                raise ValueError(f"{key} is duplicate")
            seen.add(key)

    @classmethod
    def _convert_and_validate(cls, pairs: list[tuple[str, str]]) -> AppConfig:
        """外部キーを内部名へ変換し、AppConfig を生成する。"""

        raw: dict[str, str] = {}
        for key, value in pairs:
            if key not in cls.key_map:
                raise ValueError(f"Unknown config key: {key}")
            raw[cls.key_map[key]] = value

        return AppConfig.model_validate_strings(raw)
