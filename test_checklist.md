# A-Maze-ing テストチェックリスト

> サブジェクト: `~/42Tokyo/pdf/A-Maze-ing/A-Maze-ing.en.subject.txt` (Version 2.0)
>
> このチェックリストは「subject に書いてあること」をそのまま並べたものではなく、**各要件が何を意味しているか・どう違反しうるか・どう検証すればその違反を確実に捕まえられるか** を考えて作っています。defense / ピア評価で詰められる観点を優先して網羅しました。
>
> 表記:
> - **要件**: subject の該当箇所に書かれていること
> - **意味**: 要件の背後にある意図と、実装が壊れたときに何が起きるか
> - **検証**: それを確実に確かめるための具体的手順 (コマンド・テスト方針)

---

## 0. 環境・前提

- [ ] **Python バージョン 3.10 以上で動く**
  - 要件: III.1「Python 3.10 or later」
  - 意味: 3.10未満では `list[str]` / `int | None` 等の組込ジェネリクス・PEP 604 構文が動かない。評価機の Python が 3.10+ のはずなので、3.9互換を保つ意味はない。
  - 検証: `python3 --version` で 3.10+ を確認。`grep -RnE "from typing import (List|Dict|Tuple|Optional|Union)" mazegen/` で 3.9 互換 import が残っていないか確認 (古い書き方が混在しているとレビューで指摘されやすい)。

- [ ] **venv 内で実行している**
  - 要件: III.3「It is recommended to use virtual environments」 / プロジェクトメモリ `feedback_use_venv.md`
  - 意味: グローバル汚染を避ける。defense 機でも venv で動かして再現する。
  - 検証: `source .venv/bin/activate && which python3` が `.venv/bin/python3` を指していること。

---

## 1. Common Instructions (Chapter III)

### 1.1 静的解析

- [ ] **flake8 がエラー0**
  - 要件: III.1「adhere to the flake8 coding standard」
  - 意味: スタイル違反は評価で機械的に減点されうる。`.flake8` で除外設定をしすぎていないかも見られる。
  - 検証: `flake8 .` の終了コード 0。`.flake8` を開いて `ignore=` に重大ルール (E9, F8 系) を入れていないか目視確認。

- [ ] **mypy がエラー0 (指定フラグ全部つき)**
  - 要件: III.2「mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs」
  - 意味: フラグを省略すると意味が変わる (特に `--disallow-untyped-defs` を抜くと型なし関数が見逃される)。Makefile の lint ルールがそのフラグで起動することが必須。
  - 検証: `make lint` の出力に上記 5 フラグが全部含まれていること、終了コード 0。

- [ ] **(任意) `make lint-strict` (`mypy . --strict`) も通る**
  - 意味: subject「strongly recommended to try --strict」。通っていれば評価で印象が良い。Strict は `Any` の暗黙利用も拒否する。
  - 検証: `make lint-strict` の終了コード 0。落ちる場合は「strict は任意なので外している」と説明できるようにしておく。

### 1.2 型ヒント・ドキュメンテーション

- [ ] **すべての関数に引数・戻り値の型ヒント**
  - 要件: III.1「include type hints for function parameters, return types, and variables」
  - 意味: 部分的に型がある状態は最悪 (mypy が型推論を諦める)。例えば `def foo(self, x): -> None` のような中途半端を残さない。
  - 検証: `grep -RnE "def [a-zA-Z_]+\(" mazegen/ a_maze_ing.py | grep -v "->"` でアロー無し関数を探す (デコレータや複数行 def は手で確認)。

- [ ] **すべての public 関数・クラスに docstring**
  - 要件: III.1「Include docstrings in functions and classes following PEP 257」
  - 意味: `__init__` / public method / class に最低 1 行の docstring がないと subject 違反。Google/NumPy スタイルで `Args:` / `Returns:` / `Raises:` を書く。
  - 検証: `pydocstyle mazegen/` または手で `class ` / `def ` 直下に文字列リテラルがあるか確認。

### 1.3 例外とリソース管理

- [ ] **例外で「クラッシュ」していない**
  - 要件: III.1「If your program crashes due to unhandled exceptions during the review, it will be considered non-functional」
  - 意味: Python のデフォルト traceback がユーザに見えたら即不合格相当。ただし「捕まえて pass する」だけでも×。捕まえた上で**意味のあるメッセージを stderr に出して非0で終了**するのが正解。
  - 検証: 後述の CLI 異常系テストで `Traceback` が出ない・終了コードが非0・`stderr` にユーザ向け文章が出ることを確認。

- [ ] **ファイル/外部リソースは context manager (`with`) で開く**
  - 要件: III.1「Prefer context managers for resources like files or connections」
  - 意味: `open()` のままだとパース中に例外が出たときファイルディスクリプタがリークする。
  - 検証: `grep -Rn "open(" mazegen/ a_maze_ing.py` で `with open(...)` 以外がないか確認。

---

## 2. Makefile (III.2)

- [ ] **`make install` で依存がインストールできる**
  - 検証: 新しい venv で `make install` → `pip list` に `requirements.txt` の中身が並ぶ。

- [ ] **`make run` でメインが起動する**
  - 検証: `make run` で `python3 a_maze_ing.py config.txt` 相当が走り、`maze.txt` が生成される。

- [ ] **`make debug` で pdb に入る**
  - 要件: III.2「debug: Run the main script in debug mode using Python's built-in debugger (e.g., pdb)」
  - 意味: 単に `python3 -O` ではなく `pdb` プロンプトが出ること。
  - 検証: `make debug` を打って `(Pdb)` プロンプトが出る。`q` で抜けられる。

- [ ] **`make clean` でキャッシュが消える**
  - 検証: `find . -name __pycache__ -o -name .mypy_cache` 実行 → `make clean` → 同じ find が空になる。

- [ ] **`make lint` が flake8 と mypy 両方を呼ぶ**
  - 意味: どちらか片方だけだと subject 違反。
  - 検証: `cat Makefile` で `lint:` ルールに `flake8 .` と `mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs` が両方あること。

---

## 3. CLI 使用法 (IV.2)

- [ ] **ファイル名が `a_maze_ing.py` で完全一致**
  - 要件: IV.2「You must use this name」
  - 意味: スペル違いで自動評価が落ちる。
  - 検証: `ls a_maze_ing.py`。

- [ ] **`python3 a_maze_ing.py config.txt` で正常終了**
  - 検証: `echo $?` が 0、`maze.txt` (OUTPUT_FILE で指定) が生成される。

- [ ] **引数 0 個 → 適切なエラー**
  - 検証: `python3 a_maze_ing.py; echo $?` で非 0、stderr に Usage 文。`Traceback` が出ない。

- [ ] **引数 2 個以上 → 適切なエラー**
  - 検証: `python3 a_maze_ing.py a b; echo $?` で非 0、Usage 文。

- [ ] **存在しない config ファイル → 適切なエラー**
  - 検証: `python3 a_maze_ing.py nope.txt` で「File not found」相当のメッセージ＋非 0 終了、`Traceback` 無し。

- [ ] **読み取り権限なし config ファイル → 適切なエラー**
  - 検証: `chmod 000 bad.txt && python3 a_maze_ing.py bad.txt` で `Permission denied` 相当のメッセージ。

- [ ] **ディレクトリを渡す → 適切なエラー**
  - 検証: `python3 a_maze_ing.py mazegen/` で `IsADirectoryError` の素生 traceback ではなく、整形メッセージ。

- [ ] **空ファイルを渡す → 適切なエラー**
  - 意味: 必須キーが全部欠ける状態と同じ。
  - 検証: `: > empty.txt && python3 a_maze_ing.py empty.txt` で「missing key WIDTH」等のメッセージ。

---

## 4. Configuration File (IV.3) — **最重要**

### 4.1 パーサの素直さ

- [ ] **`KEY=VALUE` 形式 1 行 1 ペアを読む**
  - 検証: 標準的な config を読み込めること。

- [ ] **`#` で始まる行は完全に無視**
  - 要件: IV.3「Lines starting with # are comments and must be ignored」
  - 意味: 行頭以外の `#` はコメントとして扱うか、値の一部として扱うかで挙動が変わる。subject 表現「starting with」は行頭限定と解釈するのが安全。
  - 検証: `# WIDTH=20\nWIDTH=10` で WIDTH=10 が採用される。`WIDTH=10 # comment` がエラーになるか正しくパースされるか、どちらの仕様か README に書いてあること。

- [ ] **空行を無視**
  - 検証: ペアの間に空行を挟んでもエラーにならない。

- [ ] **`=` 周りの空白を許容**
  - 意味: 既存の `config.txt` に `ENTRY = 0,0` という空白入りの記述がある以上、サポートしないと自分の同梱ファイルでクラッシュする。
  - 検証: `WIDTH = 10 ` (前後・両端空白) でも 10 として解釈される。

- [ ] **行末空白・タブ混入で壊れない**
  - 検証: `WIDTH=10\t\n` でも 10 と解釈。

### 4.2 必須キーの欠落

- [ ] **WIDTH 欠落 → エラー**
- [ ] **HEIGHT 欠落 → エラー**
- [ ] **ENTRY 欠落 → エラー**
- [ ] **EXIT 欠落 → エラー**
- [ ] **OUTPUT_FILE 欠落 → エラー**
- [ ] **PERFECT 欠落 → エラー**
  - 要件: IV.3 表「The following keys are mandatory」
  - 意味: 6 個全部欠落チェックを別々にやる (まとめて「必須キー欠落」だけだと、ある 1 個だけ欠けたときの個別メッセージが分かりにくい)。
  - 検証: 各キーを 1 つずつコメントアウトして実行、それぞれエラーメッセージにキー名が含まれること。

### 4.3 値の妥当性

- [ ] **WIDTH/HEIGHT が整数でない → エラー**
  - 検証: `WIDTH=abc`, `WIDTH=1.5`, `WIDTH=` の各ケースで非 0 終了。

- [ ] **WIDTH/HEIGHT が 0 以下 → エラー**
  - 意味: 0 や負数で進むと迷路がそもそも作れない。
  - 検証: `WIDTH=0`, `WIDTH=-3` で拒否。

- [ ] **ENTRY/EXIT が `x,y` 形式以外 → エラー**
  - 検証: `ENTRY=0,0,0`, `ENTRY=0`, `ENTRY=a,b` を拒否。

- [ ] **ENTRY と EXIT が等しい → エラー**
  - 要件: IV.4「Entry and exit exist and are different」
  - 意味: ピア評価でほぼ確実に試される境界。
  - 検証: `ENTRY=0,0` `EXIT=0,0` で非 0 終了。

- [ ] **ENTRY/EXIT が範囲外 → エラー**
  - 検証: `WIDTH=10` `ENTRY=10,0` (上限境界), `ENTRY=-1,0` (負) を拒否。

- [ ] **PERFECT の値が `True`/`False` 以外**
  - 意味: `true` / `1` / `yes` を許すかどうかは仕様次第。subject にぶれる余地があるので**自分の仕様を README に明記**しておく。
  - 検証: 仕様通りに受理／拒否される。

### 4.4 その他

- [ ] **重複キーの挙動が定義されている**
  - 検証: `WIDTH=10\nWIDTH=20` のとき「最後勝ち / エラー」のどちらかに統一されている (README に書く)。

- [ ] **未知のキーでクラッシュしない**
  - 意味: 将来 `SEED` / `ALGORITHM` 等を追加したときに既存ファイルが壊れないように。subject「You may add additional keys」を支える性質。
  - 検証: `FOOBAR=baz` を含む config で警告を出すなり無視するなり、クラッシュしない。

- [ ] **デフォルト config がリポジトリ root にある**
  - 要件: IV.3「A default configuration file must be available in your Git repository」
  - 検証: `ls config.txt` (現状ある)。

---

## 5. Maze Requirements (IV.4) — **最重要**

### 5.1 乱数性・再現性

- [ ] **seed を固定すると同じ迷路が出る**
  - 要件: IV.4「reproducibility via a seed is required」
  - 意味: defense で「同じ seed で 2 回回して」と言われる頻出ポイント。
  - 検証: `SEED=42` で 2 回実行 → `diff maze1.txt maze2.txt` が空。

- [ ] **seed を変えると別の迷路が出る**
  - 検証: `SEED=42` と `SEED=43` で diff が非空。

- [ ] **seed なし (省略時) は実行ごとに変わる**
  - 検証: 連続 2 回実行で diff が非空 (低確率で同一になる可能性は無視)。

### 5.2 セル単位の妥当性

- [ ] **各セルの壁は 0〜4 個 (N/E/S/W のみ)**
  - 検証: 出力 hex を読み、各文字が `0`〜`F` の範囲内であること、内部表現も 4 ビット内に収まる。

- [ ] **隣接セルの壁が一致する (coherence)**
  - 要件: IV.4「each neighbouring cell must have the same wall if any」
  - 意味: ここが崩れると視覚表現と hex 表現が矛盾し validation script で即落ちる。**最も注意すべき性質**。
  - 検証: 全 `(x,y)` について
    - `cell(x,y).E == cell(x+1,y).W` (右隣)
    - `cell(x,y).S == cell(x,y+1).N` (下隣)
    を assert するテストを書く。失敗したら座標と両セルの hex を表示する。

- [ ] **外周セルの外向き壁がすべて閉じている**
  - 要件: IV.4「there must be walls at the external borders」
  - 意味: ENTRY/EXIT は「壁が抜けている」のではなく「entry/exit 概念」として別レイヤで持つ設計が安全 (壁を抜くと連結性チェックが壊れる)。
  - 検証: `y=0` の全セルで N 壁=1、`y=H-1` で S=1、`x=0` で W=1、`x=W-1` で E=1。

### 5.3 連結性・形状

- [ ] **entry から全セルに到達できる (42 パターン除く)**
  - 要件: IV.4「The structure ensures full connectivity and no isolated cells (except the '42' pattern)」
  - 検証: BFS して訪問数 == `WIDTH*HEIGHT - (42パターンで孤立化したセル数)`。

- [ ] **孤立セル/孤立島が無い**
  - 検証: 上の BFS と表裏。BFS 結果に含まれないセルが 42 パターン以外に存在しないこと。

- [ ] **3x3 以上の開口が存在しない**
  - 要件: IV.4「Corridors can't be wider than 2 cells. ... never a 3x3 open area」
  - 意味: subject に「2x3, 3x2 はOK」と明記。境界条件 `2x3 OK / 3x3 NG` をピンポイントで試す。
  - 検証: 全 `(x,y)` を左上として 3x3 ブロックを取り、その内側 `(2x2)` の壁がすべて開いている (= 9 セルの間の 12 個の壁がすべて open) ケースが 1 つでもあれば NG。

### 5.4 "42" パターン

- [ ] **視覚表現に "42" が読み取れる**
  - 要件: IV.4「the maze must contain a visible "42" drawn by several fully closed cells」
  - 意味: 「fully closed cells」= 4 壁すべて閉のセル群で文字を形作る。視覚表現で見えなければ意味なし。
  - 検証: ASCII レンダリングのスクリーンショットで実際に「4」「2」が読める。

- [ ] **42 を構成するセルが「fully closed」**
  - 検証: 42 形を構成するセルの hex が `F` (1111) になっている。

- [ ] **小さすぎる迷路では 42 を省略し、コンソールにエラーメッセージ**
  - 要件: IV.4 注釈「The "42" pattern may be omitted in case the maze size does not allow it (i.e. too small). Print an error message on the console in that case」
  - 意味: クラッシュではなく「省略しました」というメッセージを出す。閾値の根拠 (例: `WIDTH < 10 or HEIGHT < 5`) を README に書く。
  - 検証: `WIDTH=3 HEIGHT=3` で実行して、迷路は生成されるが stderr に省略メッセージが出る。

### 5.5 PERFECT モード

- [ ] **PERFECT=True で entry→exit のパスが唯一**
  - 要件: IV.4「the maze must contain exactly one path between the entry and the exit」
  - 意味: 厳密には「全域木 (spanning tree)」になっていること。閉路があれば複数経路ができる。
  - 検証: entry → exit の単純パスを DFS で全列挙し、本数 == 1 を確認。または「壁を取り除いた隣接グラフが森 (= |V|-1 本の辺) になっているか」を確認。

- [ ] **PERFECT=False では複数経路があり得る**
  - 意味: 必須ではないが、PERFECT フラグの差が出ていることを確認。
  - 検証: 同じ seed で PERFECT を切り替え、片方で複数経路が出ること。

### 5.6 サイズ境界

- [ ] **WIDTH=1 / HEIGHT=1 / 1x1 で落ちない (もしくは仕様で拒否)**
  - 意味: subject は最小サイズを明示していないので、自分の仕様 (例: 最小 5x5) を README に書いた上で拒否するのが無難。
  - 検証: 仕様通りに動く / 拒否される。

- [ ] **WIDTH=2 HEIGHT=2 (小サイズ) で動く**
  - 検証: 42 省略メッセージが出つつ、迷路は妥当。

- [ ] **WIDTH=100 HEIGHT=100 (大サイズ) で現実的時間内に終わる**
  - 意味: アルゴリズム選定 (Prim/Kruskal/recursive backtracker) によって速度がまったく違う。defense で「大きいサイズで」と振られる可能性あり。
  - 検証: `time make run` で数秒〜十数秒以内。

---

## 6. Output File Format (IV.5) — **最重要**

### 6.1 hex エンコーディング

- [ ] **bit 0=N, 1=E, 2=S, 3=W, 1=closed, 0=open**
  - 要件: IV.5 表
  - 意味: bit 順を間違えると **全部の hex 値が反転状態になる**ので、validation script で即不合格。
  - 検証: 手で 1 セル選び、視覚表現の壁の有無と hex 値を bit 単位で照合 (例: 北・西だけ閉なら 1001 = 9)。

- [ ] **subject 例「3 = 0011」「A = 1010」が一致する**
  - 検証: 上のチェックを subject の例題で再確認 (`3 = N+E closed` / `A = E+W closed`)。
  - 注意: 「3」は subject 本文が「open to the south and west」と書いており、表と矛盾している可能性がある。実際には「bit 0 (N) = 1, bit 1 (E) = 1 → N と E が閉、S と W が開」と読むのが整合的。**自分の解釈を README に明記**。

### 6.2 ファイル全体の構造

- [ ] **HEIGHT 行の hex データ → 空行 → entry → exit → path の順**
  - 要件: IV.5「After an empty line, the following 3 elements are inserted in the output file on 3 lines: the entry coordinates, the exit coordinates, and the shortest valid path」
  - 意味: 空行の有無、3 要素の順序を間違えやすい。
  - 検証: 出力ファイルを開いて目視 + 行数チェック (`wc -l`)。

- [ ] **各行が `\n` で終わる**
  - 意味: `\r\n` だと Linux 環境のテストツールが壊れることがある。最終行の改行抜けも grader によっては落ちる。
  - 検証: `xxd maze.txt | tail` で `0a` 終端を確認。`file maze.txt` が `ASCII text`。

- [ ] **path 文字列は N/E/S/W のみで構成**
  - 検証: `grep -E '^[NESW]+$' <(tail -1 maze.txt)` がマッチ。

- [ ] **path に従って歩くと壁を抜けず entry → exit に到達する**
  - 意味: hex と path が乖離していたら無意味。シミュレータを書いて検証。
  - 検証: pytest で hex から壁を再構築 → path を一文字ずつ追って、壁衝突がないか・最終地点が exit か。

- [ ] **path が最短経路 (BFS と同じ長さ)**
  - 要件: IV.5「the shortest valid path」
  - 意味: 「valid な path」だけでは不十分、**最短**。
  - 検証: hex から BFS で最短距離を計算し、`len(path) == bfs_distance`。

### 6.3 validation script

- [ ] **subject 添付の validation script を通る**
  - 要件: IV.5「a validation script is provided with this subject to control that the output file contains coherent data」
  - 意味: pdf 添付の script があるはず。リポジトリに同梱されていれば必ず実行する。
  - 検証: スクリプトを `python3 validate.py maze.txt config.txt` 等で実行し、エラー 0。

---

## 7. Visual Representation (Chapter V)

- [ ] **ASCII または MLX のいずれかで表示できる**
  - 検証: 起動して画面に迷路が出る。

- [ ] **壁・entry・exit・解の経路が視覚的に区別できる**
  - 要件: V「The visual should clearly show walls, entry, exit, and the solution path」
  - 検証: スクリーンショットで 4 要素が判別できる。色分けやマーカーが README に説明されている。

### インタラクション (V)

- [ ] **再生成キー: 別の迷路を生成して描画**
- [ ] **解パスの表示/非表示トグル**
- [ ] **壁色変更**
- [ ] **(任意) 42 パターン専用色**
  - 意味: 4 つすべてキーバインドが README に書かれていること。defense で評価者が触れる。
  - 検証: 各キーを押して挙動を確認。

- [ ] **端末/ウインドウサイズより大きい迷路でクラッシュしない**
  - 意味: スクロール対応または「大きすぎます」のメッセージ。
  - 検証: `WIDTH=200 HEIGHT=200` で起動。

---

## 8. Code Reusability (Chapter VI)

- [ ] **`MazeGenerator` 相当クラスが 1 つの独立モジュールにある**
  - 要件: VI「You must implement the maze generation as a unique class ... inside a standalone module」
  - 意味: visualizer や CLI と疎結合になっている。`MazeGenerator` 単体を import して使えるはず。
  - 検証: `python3 -c "from mazegen import MazeGenerator; m = MazeGenerator(width=10, height=10, seed=42); m.generate(); print(m.get_solution())"` が動く。

- [ ] **README に最小サンプルコードが載っている**
  - 要件: VI「a basic example」
  - 検証: README をコピペして実際に動く。

- [ ] **カスタムパラメータ (size, seed) を渡せる**
  - 検証: 上記 import で渡せる。

- [ ] **生成後に「構造」と「解」にアクセスできる**
  - 要件: VI「Access the generated structure, and access at least a solution」
  - 注: 「構造の format は出力ファイルと同じである必要はない」(VI 注釈)。
  - 検証: `m.maze` / `m.solution` などのアクセサがある。

- [ ] **リポジトリ root に `mazegen-*.whl` または `mazegen-*.tar.gz` がある**
  - 要件: VI「This package must be called mazegen-* and the file must be located at the root of your git repository」
  - 検証: `ls mazegen-*.whl mazegen-*.tar.gz` で 1 つ以上ヒット。
  - 注意: 現状 `ls` で見当たらない可能性あり → 要確認。

- [ ] **ソースから再ビルドできる**
  - 要件: VI「install the needed tools and build your package again from your sources」
  - 意味: defense で「もう 1 回ビルドして」と言われたときに `python -m build` 等で `mazegen-*.whl` が再生成できる。`pyproject.toml` が必要。
  - 検証: 新しい venv で `pip install build && python -m build` → `dist/mazegen-*.whl` が生成。

- [ ] **ビルド済みパッケージを別 venv に pip install できる**
  - 検証: `python -m venv /tmp/v && /tmp/v/bin/pip install ./mazegen-*.whl && /tmp/v/bin/python -c "import mazegen"`。

---

## 9. README (Chapter VII)

- [ ] **1 行目が斜体で `*This project has been created as part of the 42 curriculum by <login1>[, <login2>...].*`**
  - 要件: VII 1 つ目の bullet
  - 意味: 厳密に「very first line」。前に空行を置いたら違反。アスタリスクで囲む (Markdown 斜体)。
  - 検証: `head -1 README.md` を目視。

- [ ] **Description セクション (目標と概要)**
- [ ] **Instructions セクション (install/build/run)**
- [ ] **Resources セクション (参考文献 + AI 利用箇所の明示)**
  - 意味: AI 利用が空欄だと subject 違反。「どのタスクで・どの部分で AI を使ったか」を最低 1 文ずつ書く。
  - 検証: `Resources` 節に AI に関する記述があること。

- [ ] **Config ファイルの完全な仕様 (キー一覧・値の制約・コメント仕様・空白許容ルール)**
- [ ] **採用したアルゴリズム名**
- [ ] **そのアルゴリズムを選んだ理由 (Prim vs Kruskal vs Recursive Backtracker の比較等)**
- [ ] **再利用可能な部分とその使い方 (= mazegen モジュールの API)**
- [ ] **チームマネジメント**
  - 各メンバーの役割
  - 当初の計画と最終的な変遷
  - うまくいった点・改善点
  - 使ったツール (Git, Trello, Discord, Claude Code 等)
- [ ] **bonus を実装している場合の説明**
  - 意味: bonus は実装しただけでは不十分、README で明示しないと採点されないことがある。

---

## 10. Bonuses (Chapter VIII)

- [ ] **複数の生成アルゴリズムが切り替えられる**
  - 検証: config の `ALGORITHM=prim/kruskal/...` 等で動く。各アルゴリズムが上記 5 章の制約を満たすことを seed 固定で確認。

- [ ] **生成アニメーション**
  - 検証: 起動時に迷路が「掘られていく」過程が描画される。

---

## 11. Submission / Defense 想定 (Chapter IX)

- [ ] **リポジトリ内のみで完結している**
  - 要件: IX「Only the work inside your repository will be evaluated」
  - 意味: ローカル環境変数や `~` 配下のファイルに依存していないこと。
  - 検証: `git clone` してきたばかりの状態で `make install && make run` が動く。

- [ ] **ファイル名スペル**
  - `a_maze_ing.py` (アンダースコアの位置に注意)
  - `README.md` (`Readme.md` でない)
  - `Makefile` (大文字 M)
  - `mazegen-*.whl` または `.tar.gz`
  - `config.txt` (任意名でよいが、デフォルト名は揃えると親切)

- [ ] **defense 改修要求への耐性**
  - 要件: IX「a brief modification of the project may occasionally be requested ... a few lines of code to write or rewrite」
  - 意味: 関心が分離されていれば数分で対応可能。例: 「path の文字を NSEW から ↑↓←→ に変えて」「外周の hex を別記号で表示して」など。
  - 検証: 主要な責務 (`ConfigLoader` / `MazeGenerator` / `MazeValidator` / `MazeSerializer` / `MazeSolver` / `Visualizer` / `MazeApp`) が別ファイルに分かれていること (現状の `mazegen/` 構成は OK)。

---

## 12. グローバル方針との整合 (CLAUDE.md / memory)

- [ ] **常に venv 内で実行している**
  - メモリ: `feedback_use_venv.md`
  - 検証: 直近のテスト実行も `.venv` から起動。

- [ ] **dev → main マージ計画がある**
  - 意味: 提出時のブランチを揃える (`master`/`main` どちらが評価対象か校舎ルール確認)。
  - 検証: `git log --oneline main..dev` で残差を確認、最終的に main に merge。

- [ ] **`.env` 等の機密ファイルを誤コミットしていない**
  - 検証: `git ls-files | grep -E "\.env$"` が空。`.gitignore` に `.env` あり。

---

## 付録: 一括検証シナリオ

defense 直前に最低限通すスクリプト (擬似)。

```bash
# 1) 環境
source .venv/bin/activate
python3 --version  # 3.10+

# 2) 静的解析
make lint
flake8 .
mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports \
       --disallow-untyped-defs --check-untyped-defs

# 3) 既定 config
make run
cat maze.txt

# 4) 異常系
python3 a_maze_ing.py            # 引数なし → エラー
python3 a_maze_ing.py nope.txt   # 不在ファイル → エラー
python3 a_maze_ing.py mazegen/   # ディレクトリ → エラー

# 5) 再現性
python3 a_maze_ing.py config_seed42.txt  # OUTPUT_FILE=m1.txt
python3 a_maze_ing.py config_seed42.txt  # OUTPUT_FILE=m2.txt
diff m1.txt m2.txt  # 空であること

# 6) 大サイズ
time python3 a_maze_ing.py config_100x100.txt

# 7) 視覚表示
make run  # 4 種のキー操作を試す

# 8) パッケージ
ls mazegen-*.whl mazegen-*.tar.gz
python -m venv /tmp/v
/tmp/v/bin/pip install ./mazegen-*.whl
/tmp/v/bin/python -c "from mazegen import MazeGenerator"
```
