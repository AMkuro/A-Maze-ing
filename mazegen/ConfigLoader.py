class AppConfig:
    width: int
    height: int
    entry: tuple[int, int]
    exit: tuple[int, int]
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
        clean_lines: list[str] = self._read_lines(filepath)
        parsed_lines: list[tuple[str, str]] = []
        for line in clean_lines:
            pair = self._parse_line(line)
            self._check_allowed_keys(pair)
            parsed_lines.append(pair)
        self._check_duplicate_keys(parsed_lines)

    def _read_lines(self, filepath: str) -> list[str]:
        """ファイルを開き,コメント/空行を除いた行リストを返す"""
        processed_line: list[str] = []
        try:
            with open(filepath, encoding="utf-8") as f:
                for line in f:
                    line = line.rstrip("\n")
                    if not line.startswith("#") and line:
                        processed_line.append(line)
        except Exception as e:
            raise e
        return processed_line

    def _parse_line(self, line: str) -> tuple[str, str]:
        """key=value形式の一行をパースしてタプルで返す"""
        splited_setting: list[str] = line.split("=")
        if len(splited_setting) != 2:
            raise ValueError("Parse format is incorrect.")
        splited_setting = [part.strip() for part in splited_setting]
        key, value = splited_setting
        return (key, value)

    def _check_duplicate_keys(self, pairs: list[tuple[str, str]]) -> None:
        """キーの重複があれば、例外を送出する"""
        seen: set[str] = set()
        for key, _ in pairs:
            if key in seen:
                raise ValueError(f"{key} is duplicate")
            seen.add(key)

    def _check_allowed_keys(self, pair: tuple[str, str]) -> None:
        """未知のキーがあれば、例外を送出する"""
        allowed_keys: set[str] = self.mandatory_keys | self.extra_keys
        if pair[0] not in allowed_keys:
            raise ValueError(f"Unknown key appeared: {pair[0]}")

    def _convert_and_validate(self, pairs: list[tuple[str, str]]) -> AppConfig:
        """値を型変換/範囲チェックしAppConfigインスタンスを生成する"""
        pass


if __name__ == "__main__":
    test = ConfigLoader()
    test_files: list[str] = [
        "error_bad_syntax.txt",
        "error_duplicate_key.txt",
        "error_missing_key.txt",
        "error_out_of_bounds.txt",
        "valid_with_comments.txt",
    ]
    # for test_file in test_files:
    # print(test._read_lines(f"../test/{test_file}"))
    print(test._parse_line(line="ENTRY = 0,0"))
