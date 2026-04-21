# 設定ファイル例

このディレクトリには、正常実行用とエラー再現用の設定ファイル例を置いています。

## 正常系

| ファイル | 目的 |
| --- | --- |
| `valid_minimal.txt` | 必須キーだけを含む最小の正常設定 |
| `valid_with_seed.txt` | `SEED` で再現可能にした正常設定 |
| `valid_with_comments.txt` | コメント行と空行を含む正常設定 |

## 構文・キーのエラー

設定ファイルの読み込み・構文解析・キー確認の段階で失敗する例です。

| ファイル | 失敗する段階 |
| --- | --- |
| `invalid_malformed_no_equals.txt` | 設定ファイルの構文 |
| `invalid_empty_key.txt` | 設定ファイルの構文 |
| `invalid_empty_value.txt` | 設定ファイルの構文 |
| `invalid_unknown_key.txt` | 設定キーの検証 |
| `invalid_algorithm_key_removed.txt` | 設定キーの検証 |
| `invalid_display_mode_key_removed.txt` | 設定キーの検証 |
| `invalid_duplicate_width.txt` | 設定キーの検証 |

## 必須キー不足

`KEY=VALUE` の形式としては正しいものの、必須キーが不足しているため
Pydantic の検証で失敗する例です。

| ファイル | 不足しているキー |
| --- | --- |
| `invalid_missing_width.txt` | `WIDTH` |
| `invalid_missing_height.txt` | `HEIGHT` |
| `invalid_missing_entry.txt` | `ENTRY` |
| `invalid_missing_exit.txt` | `EXIT` |
| `invalid_missing_output_file.txt` | `OUTPUT_FILE` |
| `invalid_missing_perfect.txt` | `PERFECT` |

## 値の検証エラー

`KEY=VALUE` の形式としては正しいものの、値が不正なため Pydantic または
カスタム validator で失敗する例です。

| ファイル | 問題 |
| --- | --- |
| `invalid_width_zero.txt` | `WIDTH` が 0 |
| `invalid_width_negative.txt` | `WIDTH` が負の値 |
| `invalid_width_not_integer.txt` | `WIDTH` が整数ではない |
| `invalid_height_zero.txt` | `HEIGHT` が 0 |
| `invalid_height_negative.txt` | `HEIGHT` が負の値 |
| `invalid_height_not_integer.txt` | `HEIGHT` が整数ではない |
| `invalid_entry_bad_format.txt` | `ENTRY` が `x,y` 形式ではない |
| `invalid_entry_not_integer.txt` | `ENTRY` に整数ではない座標が含まれる |
| `invalid_entry_out_of_bounds.txt` | `ENTRY` が迷路の範囲外 |
| `invalid_exit_bad_format.txt` | `EXIT` が `x,y` 形式ではない |
| `invalid_exit_not_integer.txt` | `EXIT` に整数ではない座標が含まれる |
| `invalid_exit_out_of_bounds.txt` | `EXIT` が迷路の範囲外 |
| `invalid_same_entry_exit.txt` | `ENTRY` と `EXIT` が同じセル |
| `invalid_output_file_bad_char.txt` | `OUTPUT_FILE` に禁止文字が含まれる |
| `invalid_perfect_not_bool.txt` | `PERFECT` が真偽値として解釈できない |
| `invalid_seed_not_integer.txt` | `SEED` が整数ではない |

## 後続処理でのエラー

設定ファイルの基本形式や値の検証は通るものの、その後の迷路生成や出力で失敗する例です。

| ファイル | 失敗する段階 |
| --- | --- |
| `invalid_single_column_maze.txt` | 迷路生成 |
| `invalid_single_row_maze.txt` | 迷路生成 |
| `invalid_output_parent_missing.txt` | 出力ファイル書き込み |
