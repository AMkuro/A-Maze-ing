*This project has been created as part of the 42 curriculum by miwasaki, shukondo*

# A-Maze-ing

## Description

本プロジェクトは、設定ファイルを入力として迷路を生成し、その最短経路を求め、課題仕様に沿った形式で出力・可視化するものである。

出力では、各セルの壁情報を 4bit / 16 進 1 文字で表現した迷路データと、入口座標、出口座標、最短経路を表す NEWS 文字列を生成する。迷路生成には DFS ベースの Recursive Backtracker を用い、`PERFECT=True` では完全迷路、`PERFECT=False` では少なくとも 1 つの閉路を持つ不完全迷路を扱う。

## Instructions

本プロジェクトは Python 3.10 以上を前提とする。

依存関係のインストールには `make` を使用する。

##### インストール:

```bash
make install
```
このコマンドは、プロジェクト直下に`.venv`を作成し、`requirements.txt`に記載された依存ライブラリをインストールする。

##### 実行:
```bash
make run
```
デフォルトでは`config.txt`を使用する。別の設定ファイルを指定する場合は、以下のように実行する。
```bash
make run CONFIG=path/to/your_config.txt
```
##### デバッグ:
```
make debug
```
##### コード品質の確認:
```
make lint
make lint--strict
```
##### 一時ファイルやキャッシュの削除:
```
make clean
```
---
## Config File Format
設定ファイルは `KEY=VALUE` 形式で記述する。
空行および `#` から始まるコメント行は無視される。
`ENTRY` と `EXIT` は `x,y` 形式で指定する。

設定例:
```text

WIDTH=15
HEIGHT=10
ENTRY=0,0
EXIT=14,9

OUTPUT_FILE=maze.txt
PERFECT=True

SEED=42
```


必須キー:

| キー | 意味 | 値の形式 |
| --- | --- | --- |
| `WIDTH` | 迷路の幅 | 正の整数 |
| `HEIGHT` | 迷路の高さ | 正の整数 |
| `ENTRY` | 入口座標 | `x,y` |
| `EXIT` | 出口座標 | `x,y` |
| `OUTPUT_FILE` | 出力ファイル名 | 文字列 |
| `PERFECT` | 完全迷路にするかどうか | `True` / `False` |

任意キー:

| キー | 意味 | 値の形式 |
| --- | --- | --- |
| `SEED` | 乱数シード | 整数 |

---
## Maze Generation
迷路生成には、スタックを用いた反復的な DFS による Recursive Backtracker を採用した。

現在セルから未訪問の隣接セルへランダムに進み、進めなくなった場合は 1 つ前の分岐へ戻ることを繰り返すことで、ループのない完全迷路を生成する。

このアルゴリズムを選んだ理由は、実装が比較的単純であり、完全迷路を自然に生成でき、Python の再帰深度制限を避けながら安定して実装できるためである。

`PERFECT=True` の場合は、すべてのセルが連結であり、かつ閉路を持たない完全迷路を生成する。
`PERFECT=False` の場合は、完全迷路生成後に追加で壁を開放することで、少なくとも 1 つの閉路を持つ不完全迷路を生成する。

ただし、この場合でも 3×3 の完全開放領域は作らないようにしている。

また、本プロジェクトでは迷路中央付近に “42” パターンを埋め込む仕組みを実装している。

このパターンは保護セルとして扱い、通常の通路生成では破壊しない。

迷路サイズが小さい場合は、このパターンを埋め込まずに通常の迷路生成のみを行う。

---
## Reusable Parts
本プロジェクトでは、迷路生成・解法・出力を独立したモジュールとして分離しており、一部のコードは別プロジェクトでも再利用できる構成としている。

特に再利用しやすい部分は以下である。

- `MazeGenerator`

  設定に基づいて迷路を生成する。サイズ、入口、出口、完全迷路か不完全迷路か、シード値などを変えて利用できる。

- `MazeSolver`

  生成済みの迷路に対して BFS により最短経路を求める。経路座標列と NEWS 文字列の両方を取得できる。

- `MazeSerializer`

  迷路の内部表現を課題仕様の出力形式へ変換する。内部表現と外部出力を分離する部品として利用できる。

- `MazeValidator`

  迷路構造が要件を満たしているかを独立に検証できる。壁整合性、外周、3×3 開放領域、不完全迷路条件などの確認に利用できる。

最小の利用例は以下の通りである。

```python

from mazegen.ConfigLoader import ConfigLoader
from mazegen.MazeGenerator import MazeGenerator
from mazegen.MazeSolver import MazeSolver
from mazegen.MazeSerializer import MazeSerializer

config = ConfigLoader().load("config.txt")
maze = MazeGenerator.generate(config)
solution = MazeSolver.solve(maze)
output = MazeSerializer.serialize(maze, solution)

print(output, end="")
```
これらのモジュールを分離していることで、可視化の有無にかかわらず、迷路生成ライブラリや探索アルゴリズムの実験用コードとして流用しやすい構成になっている。

---
## Team and Project Management

### 役割

- `shukondo`
  迷路生成アルゴリズムの検討と実装、`MazeGenerator`、`MazeSolver`、`README`、パッケージ化を担当した。

- `miwasaki`
  関数設計の整理、`ConfigLoader`、`MazeApp`、`MazeValidator` の初期版、`Visualizer` を担当した。

### 計画とその遷移

開発初期には、Notion を用いて関数単位の設計や責務分割を整理し、その内容をもとに各自が担当部分を実装する方針を立てた。
GitHub ではクラス単位またはトピック単位でブランチを分け、衝突を減らしながら並行して開発を進めた。

開発途中では、`dev` ブランチにテストや途中実装が集まりすぎたことで、`main` への反映がしづらくなるという問題が生じた。
そのため、`main` を最新版、`dev` をテスト用ブランチとして扱い、`main` の更新を `dev` に反映する運用へ変更した。

### うまくいったこと

役割分担は比較的うまく機能した。
特に、アルゴリズム理解を要する部分と、アプリケーション構成や表示系の部分を分けて担当したことで、実装を並行して進めやすかった。
また、Notion による設計整理や GitHub を用いたブランチ運用により、作業内容を共有しやすかった。

### 反省点

- GitHub の運用ルールを最初の段階でもう少し厳密に決めておくべきだった。
- `main` / `dev` / feature branch の役割分担を早い段階で明文化しておくと、後半の調整コストを減らせたと考えられる。
- スケジュール共有や、どの機能が未完了かの確認をより細かく行う余地があった。

### 使用ツール

- GitHub
- Notion
- Discord
- ChatGPT, Gemini などの AI ツール

---
## AI利用について
本プロジェクトでは、開発補助および文書整理のために AI ツールを利用した。

主な利用内容は、要件整理、設計レビュー、テスト観点整理、README の章立て整理、デバッグ時の原因候補整理、説明文の改善である。

AI ツールはあくまで補助的な支援手段として用い、出力内容をそのまま無条件に採用しない方針を取った。実際のコード、課題仕様、実行結果と照合しながら確認したうえで採用している。

特に、アルゴリズムの説明、`Validator` の判定条件、`Serializer` の出力形式、座標系の扱いなどについては、提案をそのまま採用せず、手元でテストしながら必要に応じて修正した。

また、チーム開発に関わる方針についても、最終的な採用可否はチーム内で確認しながら決定した。

---
## Resources
### 公式資料
- 42subject PDF
- [Pydantic Docs](https://pydantic.dev/docs/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)

### 記事・チュートリアル

- [【Pyxel】DFSを使ってランダムにダンジョンを生成する！](https://qiita.com/Prosamo/items/40f3847240f473edb209)
- [Maze Algorithms](https://www.jamisbuck.org/mazes/)
- [Maze Generation: Recursive Backtracking](https://weblog.jamisbuck.org/2010/12/27/maze-generation-recursive-backtracking)
- [Pydantic入門 – Pythonでシンプルかつ強力なバリデーションを始めよう](https://qiita.com/Tadataka_Takahashi/items/8b28f49d67d7e1d65d11)
- 競技プログラミングの鉄則 アルゴリズム力と思考力を高める77の技術 (Compass Booksシリーズ), マイナビ出版
