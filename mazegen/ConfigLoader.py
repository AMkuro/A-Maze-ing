from pathlib import Path
from typing_extensions import Self
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)
from typing import ClassVar


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    width: int = Field(gt=0)
    height: int = Field(gt=0)
    entry: tuple[int, int]
    exit: tuple[int, int]
    output_file: str
    perfect: bool
    seed: int | None = None

    @field_validator("entry", "exit", mode="before")
    @classmethod
    def parse_point(cls, value: object) -> object:
        if isinstance(value, str):
            parts: list[str] = value.split(",")
            if len(parts) != 2:
                raise ValueError(
                    "must be coordinates in x,y format."
                )
            x_str, y_str = parts
            try:
                return (int(y_str.strip()), int(x_str.strip()))
            except ValueError:
                raise ValueError(
                    "must be coordinates in x,y format."
                ) from None
        return value

    _forbidden_file_chars: ClassVar[frozenset[str]] = frozenset(
        '\x00\n\r<>|*?"'
    )

    @field_validator("output_file")
    @classmethod
    def validate_output_file(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("OUTPUT_FILE must not be empty.")
        bad: set[str] = set(value) & AppConfig._forbidden_file_chars
        if bad:
            raise ValueError(
                "OUTPUT_FILE contains invalid characters: "
                f"{sorted(bad)!r}."
            )
        return value

    @model_validator(mode="after")
    def validate_positions(self) -> Self:
        for name, (y, x) in (("entry", self.entry), ("exit", self.exit)):
            if not (0 <= x < self.width and 0 <= y < self.height):
                raise ValueError(
                    f"{name.upper()} must be inside the maze bounds."
                )
        if self.entry == self.exit:
            raise ValueError("ENTRY and EXIT must be different.")
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
    }

    def load(self, filepath: str) -> AppConfig:
        """ファイル読み込みからバリデーションまで一連の処理を実行しAppConfigを返す"""
        clean_lines: list[tuple[int, str]] = self._read_lines(filepath)
        parsed_lines: list[tuple[str, str]] = []
        for line_number, line in clean_lines:
            pair = self._parse_line(line_number, line)
            parsed_lines.append(pair)
        self._check_duplicate_keys(parsed_lines)
        return self._convert_and_validate(parsed_lines)

    def _read_lines(self, filepath: str) -> list[tuple[int, str]]:
        """ファイルを開き,コメント/空行を除いた行リストを返す"""
        processed_line: list[tuple[int, str]] = []
        try:
            with open(filepath, encoding="utf-8") as f:
                for line_number, line in enumerate(f, 1):
                    line = line.rstrip("\n").strip()
                    if not line.startswith("#") and line:
                        processed_line.append((line_number, line))
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Configuration file not found: {filepath}"
            ) from e
        except OSError as e:
            raise OSError(
                f"Could not read configuration file: {filepath}"
            ) from e
        return processed_line

    @staticmethod
    def _parse_line(line_number: int, line: str) -> tuple[str, str]:
        """key=value形式の一行をパースしてタプルで返す"""
        key_value: list[str] = line.split("=", 1)
        if len(key_value) != 2:
            raise ValueError(
                f"Invalid config line {line_number}: expected KEY=VALUE."
            )
        key, value = (part.strip() for part in key_value)
        if not key:
            raise ValueError(
                f"Invalid config line {line_number}: key must not be empty."
            )
        if not value:
            raise ValueError(
                f"Invalid config line {line_number}: value must not be empty."
            )
        return (key, value)

    @staticmethod
    def _check_duplicate_keys(pairs: list[tuple[str, str]]) -> None:
        """キーの重複があれば、例外を送出する"""
        seen: set[str] = set()
        for key, _ in pairs:
            if key in seen:
                raise ValueError(f"Duplicate config key: {key}.")
            seen.add(key)

    @classmethod
    def _convert_and_validate(cls, pairs: list[tuple[str, str]]) -> AppConfig:
        """外部キーを内部名へ変換し、AppConfig を生成する。"""

        raw: dict[str, str] = {}
        for key, value in pairs:
            if key not in cls.key_map:
                raise ValueError(f"Unknown config key: {key}.")
            raw[cls.key_map[key]] = value

        try:
            return AppConfig.model_validate_strings(raw)
        except ValidationError as e:
            raise ValueError(cls._validation_message(e)) from e

    @classmethod
    def _validation_message(cls, error: ValidationError) -> str:
        first_error = error.errors()[0]
        message = str(first_error.get("msg", "Invalid configuration."))
        message = message.removeprefix("Value error, ")

        if first_error.get("type") == "missing":
            location = first_error.get("loc", ())
            field = str(location[0]) if location else ""
            return f"Missing required config key: {cls._external_key(field)}."

        location = first_error.get("loc", ())
        field = str(location[0]) if location else ""
        if field:
            return f"{cls._external_key(field)}: {message}"
        return message

    @classmethod
    def _external_key(cls, internal_key: str) -> str:
        for external_key, field_name in cls.key_map.items():
            if field_name == internal_key:
                return external_key
        return internal_key.upper()
