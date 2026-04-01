"""
ConfigLoader のテストスイート

テスト対象:
  - ConfigLoader._read_lines      : コメント・空行フィルタリング
  - ConfigLoader._parse_line      : KEY=VALUE パース
  - ConfigLoader._check_duplicate_keys : 重複キー検出
  - ConfigLoader._convert_and_validate : キー変換 + Pydantic バリデーション
  - AppConfig                     : 各フィールドバリデーション
  - ConfigLoader.load             : エンド・ツー・エンド (既存テストファイル使用)
"""

import pytest
from pathlib import Path
from pydantic import ValidationError

from ConfigLoader import ConfigLoader, AppConfig

# テストファイルが置かれているディレクトリ
TEST_DIR = Path(__file__).resolve().parent


# ──────────────────────────────────────────────────────────────────────────────
# _read_lines
# ──────────────────────────────────────────────────────────────────────────────
class TestReadLines:
    """ConfigLoader._read_lines のテスト"""

    def test_filters_comment_lines(self, tmp_path: Path) -> None:
        """# で始まる行はフィルタアウトされる"""
        cfg = tmp_path / "c.txt"
        cfg.write_text("# comment\nWIDTH=10\n")
        result = ConfigLoader()._read_lines(str(cfg))
        assert result == ["WIDTH=10"]

    def test_filters_empty_lines(self, tmp_path: Path) -> None:
        """空行はフィルタアウトされる"""
        cfg = tmp_path / "c.txt"
        cfg.write_text("WIDTH=10\n\nHEIGHT=10\n")
        result = ConfigLoader()._read_lines(str(cfg))
        assert result == ["WIDTH=10", "HEIGHT=10"]

    def test_preserves_content_lines(self, tmp_path: Path) -> None:
        """有効な行はそのまま保持される"""
        cfg = tmp_path / "c.txt"
        cfg.write_text("WIDTH=10\nHEIGHT=15\n")
        result = ConfigLoader()._read_lines(str(cfg))
        assert result == ["WIDTH=10", "HEIGHT=15"]

    def test_strips_trailing_newline(self, tmp_path: Path) -> None:
        """末尾の \\n は削除される（Windowsの \\r\\n ではなく \\n のみ）"""
        cfg = tmp_path / "c.txt"
        cfg.write_text("WIDTH=10\n")
        result = ConfigLoader()._read_lines(str(cfg))
        assert result == ["WIDTH=10"]

    def test_file_not_found_raises(self) -> None:
        """存在しないファイルは FileNotFoundError を送出する"""
        with pytest.raises(FileNotFoundError):
            ConfigLoader()._read_lines("/nonexistent/path/config.txt")

    def test_mixed_content(self, tmp_path: Path) -> None:
        """コメント・空行・有効行が混在した場合、有効行のみ返す"""
        cfg = tmp_path / "c.txt"
        cfg.write_text("# header\n\nWIDTH=10\n# mid comment\nHEIGHT=15\n\n")
        result = ConfigLoader()._read_lines(str(cfg))
        assert result == ["WIDTH=10", "HEIGHT=15"]

    def test_whitespace_only_line_is_filtered(self, tmp_path: Path) -> None:
        """スペースのみの行は strip() によりフィルタアウトされる（修正済み）"""
        cfg = tmp_path / "c.txt"
        cfg.write_text("WIDTH=10\n   \nHEIGHT=15\n")
        result = ConfigLoader()._read_lines(str(cfg))
        assert result == ["WIDTH=10", "HEIGHT=15"]


# ──────────────────────────────────────────────────────────────────────────────
# _parse_line
# ──────────────────────────────────────────────────────────────────────────────
class TestParseLine:
    """ConfigLoader._parse_line のテスト"""

    def test_simple_key_value(self) -> None:
        """KEY=VALUE を正しくパースする"""
        assert ConfigLoader._parse_line("WIDTH=10") == ("WIDTH", "10")

    def test_strips_whitespace_around_equals(self) -> None:
        """= の前後のスペースは除去される"""
        assert ConfigLoader._parse_line("ENTRY = 0,0") == ("ENTRY", "0,0")

    def test_value_containing_equals(self) -> None:
        """値に = が含まれても maxsplit=1 で正しく分割される"""
        assert ConfigLoader._parse_line("OUTPUT_FILE=path/to=file.txt") == (
            "OUTPUT_FILE",
            "path/to=file.txt",
        )

    def test_no_equals_sign_raises(self) -> None:
        """= のない行は ValueError を送出する"""
        with pytest.raises(ValueError, match="Parse format is incorrect"):
            ConfigLoader._parse_line("ENTRY 0,0")

    def test_empty_key_raises(self) -> None:
        """=value のようにキーが空の場合 ValueError を送出する"""
        with pytest.raises(ValueError, match="Config key must not be empty"):
            ConfigLoader._parse_line("=value")

    def test_empty_value_is_allowed(self) -> None:
        """KEY= のように値が空でもパース自体は通る（バリデーションは後工程）"""
        assert ConfigLoader._parse_line("OUTPUT_FILE=") == ("OUTPUT_FILE", "")

    def test_coordinate_value(self) -> None:
        """座標形式 (x,y) の値を正しくパースする"""
        assert ConfigLoader._parse_line("ENTRY=0,0") == ("ENTRY", "0,0")

    def test_whitespace_only_line_raises(self) -> None:
        """スペースのみの行（_read_lines で弾かれず流れてきた場合）は ValueError"""
        with pytest.raises(ValueError, match="Parse format is incorrect"):
            ConfigLoader._parse_line("   ")


# ──────────────────────────────────────────────────────────────────────────────
# _check_duplicate_keys
# ──────────────────────────────────────────────────────────────────────────────
class TestCheckDuplicateKeys:
    """ConfigLoader._check_duplicate_keys のテスト"""

    def test_unique_keys_passes(self) -> None:
        """重複なしの場合は例外を送出しない"""
        ConfigLoader._check_duplicate_keys([("WIDTH", "10"), ("HEIGHT", "15")])

    def test_duplicate_key_raises(self) -> None:
        """重複キーがあると ValueError を送出する"""
        pairs = [("WIDTH", "10"), ("HEIGHT", "15"), ("WIDTH", "20")]
        with pytest.raises(ValueError, match="WIDTH is duplicate"):
            ConfigLoader._check_duplicate_keys(pairs)

    def test_empty_list_passes(self) -> None:
        """空リストは有効"""
        ConfigLoader._check_duplicate_keys([])

    def test_single_pair_passes(self) -> None:
        """ペアが1つだけなら重複しない"""
        ConfigLoader._check_duplicate_keys([("WIDTH", "10")])


# ──────────────────────────────────────────────────────────────────────────────
# _convert_and_validate
# ──────────────────────────────────────────────────────────────────────────────
class TestConvertAndValidate:
    """ConfigLoader._convert_and_validate のテスト"""

    def _minimal_pairs(self) -> list[tuple[str, str]]:
        return [
            ("WIDTH", "20"),
            ("HEIGHT", "15"),
            ("ENTRY", "0,0"),
            ("EXIT", "19,14"),
            ("OUTPUT_FILE", "maze.txt"),
            ("PERFECT", "True"),
        ]

    def test_valid_pairs_return_app_config(self) -> None:
        """有効なペアリストから AppConfig が返される"""
        config = ConfigLoader._convert_and_validate(self._minimal_pairs())
        assert config.width == 20
        assert config.height == 15
        assert config.entry == (0, 0)
        assert config.exit == (19, 14)
        assert config.output_file == "maze.txt"
        assert config.perfect is True

    def test_unknown_key_raises(self) -> None:
        """key_map にないキーは ValueError を送出する"""
        pairs = self._minimal_pairs() + [("UNKNOWN_KEY", "value")]
        with pytest.raises(ValueError, match="Unknown config key: UNKNOWN_KEY"):
            ConfigLoader._convert_and_validate(pairs)

    def test_perfect_false(self) -> None:
        """PERFECT=False が bool False として解釈される"""
        pairs = [(k, "False" if k == "PERFECT" else v) for k, v in self._minimal_pairs()]
        config = ConfigLoader._convert_and_validate(pairs)
        assert config.perfect is False

    def test_optional_seed(self) -> None:
        """SEED が指定された場合、int として設定される"""
        pairs = self._minimal_pairs() + [("SEED", "42")]
        config = ConfigLoader._convert_and_validate(pairs)
        assert config.seed == 42

    def test_optional_algorithm(self) -> None:
        """ALGORITHM=prim が正しく設定される"""
        pairs = self._minimal_pairs() + [("ALGORITHM", "prim")]
        config = ConfigLoader._convert_and_validate(pairs)
        assert config.algorithm == "prim"

    def test_invalid_algorithm_raises(self) -> None:
        """Literal に含まれないアルゴリズム名は ValidationError を送出する"""
        pairs = self._minimal_pairs() + [("ALGORITHM", "bfs")]
        with pytest.raises(ValidationError):
            ConfigLoader._convert_and_validate(pairs)


# ──────────────────────────────────────────────────────────────────────────────
# AppConfig
# ──────────────────────────────────────────────────────────────────────────────
class TestAppConfig:
    """AppConfig の Pydantic バリデーションテスト"""

    def _base(self) -> dict:
        return {
            "width": 20,
            "height": 15,
            "entry": (0, 0),
            "exit": (19, 14),
            "output_file": "maze.txt",
            "perfect": True,
        }

    def test_valid_config(self) -> None:
        """有効なデータで AppConfig が生成できる"""
        AppConfig(**self._base())

    def test_entry_x_out_of_bounds(self) -> None:
        """ENTRY の x が width 以上で ValidationError"""
        d = self._base()
        d["entry"] = (20, 0)  # x == width (0-indexed: 0..19)
        with pytest.raises(ValidationError, match="entry is out of bounds"):
            AppConfig(**d)

    def test_entry_y_out_of_bounds(self) -> None:
        """ENTRY の y が height 以上で ValidationError"""
        d = self._base()
        d["entry"] = (0, 15)  # y == height
        with pytest.raises(ValidationError, match="entry is out of bounds"):
            AppConfig(**d)

    def test_entry_negative_raises(self) -> None:
        """負の ENTRY 座標は out of bounds"""
        d = self._base()
        d["entry"] = (-1, 0)
        with pytest.raises(ValidationError, match="entry is out of bounds"):
            AppConfig(**d)

    def test_exit_out_of_bounds(self) -> None:
        """EXIT が範囲外で ValidationError"""
        d = self._base()
        d["exit"] = (0, 20)
        with pytest.raises(ValidationError, match="exit is out of bounds"):
            AppConfig(**d)

    def test_entry_equals_exit_raises(self) -> None:
        """ENTRY == EXIT は ValidationError"""
        d = self._base()
        d["exit"] = (0, 0)
        with pytest.raises(ValidationError, match="entry and exit must be different"):
            AppConfig(**d)

    def test_zero_width_raises(self) -> None:
        """WIDTH=0 は ValidationError (gt=0)"""
        d = self._base()
        d["width"] = 0
        with pytest.raises(ValidationError):
            AppConfig(**d)

    def test_negative_width_raises(self) -> None:
        """WIDTH=-1 は ValidationError (gt=0)"""
        d = self._base()
        d["width"] = -1
        with pytest.raises(ValidationError):
            AppConfig(**d)

    def test_zero_height_raises(self) -> None:
        """HEIGHT=0 は ValidationError (gt=0)"""
        d = self._base()
        d["height"] = 0
        with pytest.raises(ValidationError):
            AppConfig(**d)

    def test_default_algorithm_is_dfs(self) -> None:
        """algorithm のデフォルト値は 'dfs'"""
        config = AppConfig(**self._base())
        assert config.algorithm == "dfs"

    def test_default_display_mode_is_ascii(self) -> None:
        """display_mode のデフォルト値は 'ascii'"""
        config = AppConfig(**self._base())
        assert config.display_mode == "ascii"

    def test_default_seed_is_none(self) -> None:
        """seed のデフォルト値は None"""
        config = AppConfig(**self._base())
        assert config.seed is None

    def test_invalid_algorithm_raises(self) -> None:
        """'bfs' は Literal に含まれないため ValidationError"""
        d = self._base()
        d["algorithm"] = "bfs"
        with pytest.raises(ValidationError):
            AppConfig(**d)

    def test_invalid_display_mode_raises(self) -> None:
        """'gui' は Literal に含まれないため ValidationError"""
        d = self._base()
        d["display_mode"] = "gui"
        with pytest.raises(ValidationError):
            AppConfig(**d)

    def test_empty_output_file_raises(self) -> None:
        """空白のみの output_file は ValidationError"""
        d = self._base()
        d["output_file"] = "   "
        with pytest.raises(ValidationError):
            AppConfig(**d)

    def test_output_path_returns_path(self) -> None:
        """output_path() が Path オブジェクトを返す"""
        config = AppConfig(**self._base())
        assert config.output_path() == Path("maze.txt")

    def test_extra_field_raises(self) -> None:
        """extra='forbid' のため未知のフィールドは ValidationError"""
        d = self._base()
        d["unknown_field"] = "value"
        with pytest.raises(ValidationError):
            AppConfig(**d)

    # -- OUTPUT_FILE 不正文字 ------------------------------------------------

    @pytest.mark.parametrize("fname,label", [
        ("file\x00name.txt", "null byte"),
        ("file\nname.txt",   "newline"),
        ("file\rname.txt",   "carriage return"),
        ("file*.txt",        "wildcard *"),
        ("file?.txt",        "question mark"),
        ("file|name.txt",    "pipe"),
        ("file<name.txt",    "less-than"),
        ("file>name.txt",    "greater-than"),
        ('file"name.txt',    "double quote"),
    ])
    def test_output_file_invalid_char_raises(self, fname: str, label: str) -> None:
        """OUTPUT_FILE に不正文字が含まれると ValidationError"""
        d = self._base()
        d["output_file"] = fname
        with pytest.raises(ValidationError, match="invalid characters"):
            AppConfig(**d)

    def test_output_file_with_path_separator_allowed(self) -> None:
        """サブディレクトリパス (output/maze.txt) は許可される"""
        d = self._base()
        d["output_file"] = "output/maze.txt"
        config = AppConfig(**d)
        assert config.output_file == "output/maze.txt"

    # -- 極端な数値 (nan / inf) は Pydantic の int 変換で弾かれる ----------

    @pytest.mark.parametrize("field,value", [
        ("width",  "inf"),
        ("width",  "nan"),
        ("height", "inf"),
        ("height", "nan"),
        ("seed",   "inf"),
        ("seed",   "nan"),
    ])
    def test_extreme_numeric_string_raises(self, field: str, value: str) -> None:
        """inf / nan 文字列は int に変換できないため ValidationError"""
        raw = {
            "width": "10", "height": "10",
            "entry": "0,0", "exit": "9,9",
            "output_file": "out.txt", "perfect": "True",
            field: value,
        }
        with pytest.raises(ValidationError):
            AppConfig.model_validate_strings(raw)

    @pytest.mark.parametrize("coord_value", ["inf,0", "nan,0", "0,inf", "0,nan"])
    def test_extreme_coordinate_string_raises(self, coord_value: str) -> None:
        """座標に inf / nan が含まれると ValidationError"""
        raw = {
            "width": "10", "height": "10",
            "entry": coord_value, "exit": "9,9",
            "output_file": "out.txt", "perfect": "True",
        }
        with pytest.raises((ValidationError, ValueError)):
            AppConfig.model_validate_strings(raw)


# ──────────────────────────────────────────────────────────────────────────────
# load (エンド・ツー・エンド)
# ──────────────────────────────────────────────────────────────────────────────
class TestLoadIntegration:
    """ConfigLoader.load の統合テスト（既存テストファイルを使用）"""

    def test_load_bad_syntax(self) -> None:
        """error_bad_syntax.txt: '=' のない行で ValueError"""
        with pytest.raises(ValueError, match="Parse format is incorrect"):
            ConfigLoader().load(str(TEST_DIR / "error_bad_syntax.txt"))

    def test_load_duplicate_key(self) -> None:
        """error_duplicate_key.txt: WIDTH が重複して ValueError"""
        with pytest.raises(ValueError, match="WIDTH is duplicate"):
            ConfigLoader().load(str(TEST_DIR / "error_duplicate_key.txt"))

    def test_load_missing_key(self) -> None:
        """error_missing_key.txt: PERFECT が欠けて ValidationError"""
        with pytest.raises(ValidationError):
            ConfigLoader().load(str(TEST_DIR / "error_missing_key.txt"))

    def test_load_out_of_bounds(self) -> None:
        """error_out_of_bounds.txt: ENTRY=15,0 が WIDTH=10 を超えて ValidationError"""
        with pytest.raises(ValidationError, match="entry is out of bounds"):
            ConfigLoader().load(str(TEST_DIR / "error_out_of_bounds.txt"))

    def test_load_valid_with_comments(self) -> None:
        """valid_with_comments.txt が正常にロードされる
        (ALGORITHM=dfs が Literal["prim", "kruskal", "dfs"] に含まれる)"""
        result = ConfigLoader().load(str(TEST_DIR / "valid_with_comments.txt"))
        assert result.width == 20
        assert result.height == 15
        assert result.seed == 42
        assert result.algorithm == "dfs"

    def test_load_file_not_found(self) -> None:
        """存在しないファイルは FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            ConfigLoader().load("/nonexistent/path/config.txt")

    def test_load_minimal_valid_config(self, tmp_path: Path) -> None:
        """最小限の有効設定ファイルを正常にロードできる"""
        cfg = tmp_path / "valid.txt"
        cfg.write_text(
            "WIDTH=20\n"
            "HEIGHT=15\n"
            "ENTRY=0,0\n"
            "EXIT=19,14\n"
            "OUTPUT_FILE=maze.txt\n"
            "PERFECT=True\n"
        )
        result = ConfigLoader().load(str(cfg))
        assert result.width == 20
        assert result.height == 15
        assert result.entry == (0, 0)
        assert result.exit == (19, 14)
        assert result.output_file == "maze.txt"
        assert result.perfect is True

    def test_load_full_valid_config_with_optional_fields(self, tmp_path: Path) -> None:
        """オプションフィールド (SEED, ALGORITHM, DISPLAY_MODE) 付きで正常ロード"""
        cfg = tmp_path / "full.txt"
        cfg.write_text(
            "WIDTH=10\n"
            "HEIGHT=10\n"
            "ENTRY=0,0\n"
            "EXIT=9,9\n"
            "OUTPUT_FILE=out.txt\n"
            "PERFECT=False\n"
            "SEED=123\n"
            "ALGORITHM=kruskal\n"
            "DISPLAY_MODE=mlx\n"
        )
        result = ConfigLoader().load(str(cfg))
        assert result.seed == 123
        assert result.algorithm == "kruskal"
        assert result.display_mode == "mlx"
        assert result.perfect is False

    def test_load_config_with_comments_and_spaces(self, tmp_path: Path) -> None:
        """コメント・空行・= 前後のスペースが含まれていても正常ロード"""
        cfg = tmp_path / "comments.txt"
        cfg.write_text(
            "# This is a comment\n"
            "WIDTH = 5\n"
            "\n"
            "HEIGHT = 5\n"
            "# Another comment\n"
            "ENTRY = 0,0\n"
            "EXIT = 4,4\n"
            "OUTPUT_FILE = out.txt\n"
            "PERFECT = True\n"
        )
        result = ConfigLoader().load(str(cfg))
        assert result.width == 5
        assert result.entry == (0, 0)

    def test_load_perfect_lowercase_true(self, tmp_path: Path) -> None:
        """PERFECT=true（小文字）も True として受け入れられる（Pydantic のコーセション）"""
        cfg = tmp_path / "c.txt"
        cfg.write_text(
            "WIDTH=5\nHEIGHT=5\nENTRY=0,0\nEXIT=4,4\n"
            "OUTPUT_FILE=out.txt\nPERFECT=true\n"
        )
        result = ConfigLoader().load(str(cfg))
        assert result.perfect is True

    def test_load_negative_entry_raises(self, tmp_path: Path) -> None:
        """ENTRY=-1,0 のような負の座標は ValidationError"""
        cfg = tmp_path / "c.txt"
        cfg.write_text(
            "WIDTH=10\nHEIGHT=10\nENTRY=-1,0\nEXIT=9,9\n"
            "OUTPUT_FILE=out.txt\nPERFECT=True\n"
        )
        with pytest.raises(ValidationError, match="entry is out of bounds"):
            ConfigLoader().load(str(cfg))

    def test_load_non_integer_width_raises(self, tmp_path: Path) -> None:
        """WIDTH=abc のような非整数値は ValidationError"""
        cfg = tmp_path / "c.txt"
        cfg.write_text(
            "WIDTH=abc\nHEIGHT=10\nENTRY=0,0\nEXIT=9,9\n"
            "OUTPUT_FILE=out.txt\nPERFECT=True\n"
        )
        with pytest.raises(ValidationError):
            ConfigLoader().load(str(cfg))

    def test_load_entry_single_value_raises(self, tmp_path: Path) -> None:
        """ENTRY=5 のように単一値のみは ValueError (x,y 形式でない)"""
        cfg = tmp_path / "c.txt"
        cfg.write_text(
            "WIDTH=10\nHEIGHT=10\nENTRY=5\nEXIT=9,9\n"
            "OUTPUT_FILE=out.txt\nPERFECT=True\n"
        )
        with pytest.raises((ValidationError, ValueError)):
            ConfigLoader().load(str(cfg))
