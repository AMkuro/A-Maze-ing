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
    """Validated application configuration.

    Attributes:
        width: Maze width in cells.
        height: Maze height in cells.
        entry: Entry position as ``(row, column)``.
        exit: Exit position as ``(row, column)``.
        output_file: Path where the serialized maze is written.
        perfect: Whether the generated maze should be perfect.
        seed: Optional seed for reproducible random generation.
    """

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
        """Parse an ``x,y`` config coordinate into internal row-column form.

        Args:
            value: Raw coordinate value from Pydantic.

        Returns:
            Parsed ``(row, column)`` tuple, or the original value when it is
            already structured.

        Raises:
            ValueError: If a string value is not in ``x,y`` integer format.
        """
        if isinstance(value, str):
            parts: list[str] = value.split(",")
            if len(parts) != 2:
                raise ValueError("must be coordinates in x,y format.")
            x_str, y_str = parts
            try:
                return (int(y_str.strip()), int(x_str.strip()))
            except ValueError:
                raise ValueError("must be coordinates are integer.") from None
        return value

    _forbidden_file_chars: ClassVar[frozenset[str]] = frozenset(
        '\x00\n\r<>|*?"'
    )

    @field_validator("perfect", mode="before")
    @classmethod
    def validate_flag(cls, value: object):
        if isinstance(value, str):
            if value == "false" or value == "False":
                return False
            if value == "true" or value == "True":
                return True
            raise ValueError("PERFECT must be True or False")
        return value

    @field_validator("output_file")
    @classmethod
    def validate_output_file(cls, value: str) -> str:
        """Validate the configured output filename.

        Args:
            value: Raw output filename.

        Returns:
            The validated output filename.

        Raises:
            ValueError: If the filename is empty or contains forbidden
                characters.
        """
        normalized = value.strip()
        if not normalized:
            raise ValueError("OUTPUT_FILE must not be empty.")
        bad: set[str] = set(value) & AppConfig._forbidden_file_chars
        if bad:
            raise ValueError(
                f"OUTPUT_FILE contains invalid characters: {sorted(bad)!r}."
            )
        return normalized

    @model_validator(mode="after")
    def validate_positions(self) -> Self:
        """Validate entry and exit positions against the maze dimensions.

        Returns:
            The validated model instance.

        Raises:
            ValueError: If entry or exit is out of bounds, or if they point to
                the same cell.
        """
        for name, (y, x) in (("entry", self.entry), ("exit", self.exit)):
            if not (0 <= x < self.width and 0 <= y < self.height):
                raise ValueError(
                    f"{name.upper()} must be inside the maze bounds."
                )
        if self.entry == self.exit:
            raise ValueError("ENTRY and EXIT must be different.")
        return self

    def output_path(self) -> Path:
        """Return the configured output path.

        Returns:
            Output filename converted to a ``Path``.
        """
        return Path(self.output_file)


class ConfigLoader:
    """Load and validate A-Maze-ing configuration files."""

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
        """Load a config file and return a validated app configuration.

        Args:
            filepath: Path to the plain text configuration file.

        Returns:
            Validated ``AppConfig`` instance.

        Raises:
            FileNotFoundError: If the config file does not exist.
            OSError: If the config file cannot be read.
            ValueError: If parsing or validation fails.
        """
        clean_lines: list[tuple[int, str]] = self._read_lines(filepath)
        parsed_lines: list[tuple[str, str]] = []
        for line_number, line in clean_lines:
            pair = self._parse_line(line_number, line)
            parsed_lines.append(pair)
        self._check_duplicate_keys(parsed_lines)
        return self._convert_and_validate(parsed_lines)

    def _read_lines(self, filepath: str) -> list[tuple[int, str]]:
        """Read meaningful lines from a config file.

        Args:
            filepath: Path to the configuration file.

        Returns:
            Tuples of original line number and stripped non-comment content.

        Raises:
            FileNotFoundError: If the config file does not exist.
            OSError: If the config file cannot be read.
        """
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
        """Parse one ``KEY=VALUE`` config line.

        Args:
            line_number: Original line number in the config file.
            line: Stripped config line content.

        Returns:
            Parsed key and value.

        Raises:
            ValueError: If the line is not ``KEY=VALUE`` or either side is
                empty.
        """
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
        """Reject duplicate config keys.

        Args:
            pairs: Parsed key-value pairs.

        Raises:
            ValueError: If the same key appears more than once.
        """
        seen: set[str] = set()
        for key, _ in pairs:
            if key in seen:
                raise ValueError(f"Duplicate config key: {key}.")
            seen.add(key)

    @classmethod
    def _convert_and_validate(cls, pairs: list[tuple[str, str]]) -> AppConfig:
        """Convert external config keys and validate values.

        Args:
            pairs: Parsed external key-value pairs.

        Returns:
            Validated ``AppConfig`` instance.

        Raises:
            ValueError: If a key is unsupported or Pydantic validation fails.
        """
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
        """Convert a Pydantic validation error to a user-facing message.

        Args:
            error: Pydantic validation error raised while building
                ``AppConfig``.

        Returns:
            Simplified error message with the external config key when
            available.
        """
        first_error = error.errors()[0]
        message = str(first_error.get("msg", "Invalid configuration."))
        message = message.removeprefix("Value error, ")

        location = first_error.get("loc", ())
        field = str(location[0]) if location else ""
        if first_error.get("type") == "missing":
            return f"Missing required config key: {cls._external_key(field)}."

        if field:
            return f"{cls._external_key(field)}: {message}"
        return message

    @classmethod
    def _external_key(cls, internal_key: str) -> str:
        """Return the config-file key for an internal AppConfig field.

        Args:
            internal_key: Internal Pydantic field name.

        Returns:
            Matching external config key, or an upper-case fallback.
        """
        for external_key, field_name in cls.key_map.items():
            if field_name == internal_key:
                return external_key
        return internal_key.upper()
