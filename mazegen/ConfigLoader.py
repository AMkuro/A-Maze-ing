class AppConfig:
    width: int
    height: int
    entry: tuple[int, int]
    goal: tuple[int, int]
    output_file: str
    perfect: bool
    seed: int | None = None
    algorithm: str = "bfs"
    display_mode: str = "ascii"


class ConfigLoader:
    mandatory_keys: set[str] = {
        "WIDTH",
        "HEIGHT",
        "ENTRY",
        "EXIT",
        "OUTPUT_FILE",
        "PERFECT",
    }
    extra_keys: set[str] = {"SEED", "ALGORITHM", "DISPLAY_MODE"}

    def load(self, filepath: str) -> AppConfig:
        """ファイル読み込みからバリデーションまで一連の処理を実行しAppConfigを返す"""
        pass

    def _read_lines(self, filepath: str) -> list[str]:
        """ファイルを開き,コメント/空行を除いた行リストを返す"""
        pass

    def _parse_line(self, line: str) -> tuple[str, str]:
        """key=value形式の一行をパースしてタプルで返す"""
        pass

    def _check_duplicates(self, pairs: list[tuple[str, str]]) -> None:
        """キーの重複があれば、例外を送出する"""
        pass

    def _convert_and_validate(self, pairs: list[tuple[str, str]]) -> AppConfig:
        """値を型変換/範囲チェックしAppConfigインスタンスを生成する"""
        pass
