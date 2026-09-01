# RoboCup@Home GPSR コマンドジェネレータ (2026) 説明書

RoboCup@Home 公式の GPSR コマンドジェネレータ
([RoboCupAtHome/CommandGenerator](https://github.com/RoboCupAtHome/CommandGenerator))
を、GUI 込みですぐ使える形にまとめたものです。

- **GUI** … ブラウザで開く画面。コマンドを 1〜5 個生成し、大きな文字で表示できます (競技本番の提示用)。
- **CLI** … 端末で動くテキスト版。QR コード生成と EGPSR セットアップ生成が使えます。
- **LLM 言い換え** … OpenAI 互換 API につなぐと、生成したコマンドを自然な別表現に言い換えられます (任意)。

---

## 1. 動作環境

| 項目 | 内容 |
|---|---|
| OS | Linux (Ubuntu 22.04 で動作確認)。macOS / Windows(WSL) でも同手順で動くはずです |
| Python | **3.12 以上が必須**。`setup.sh` が [uv](https://docs.astral.sh/uv) 経由で自動的に用意するので、PC 側に 3.12 が無くても構いません |
| その他 | `git`, `curl`, ブラウザ |
| ネットワーク | インストール時のみ必要。**インストール後はオフラインで動きます** (LLM 言い換えを使う場合を除く) |

> Python 3.12 が必要な理由: 上流の `llm.py` が Python 3.12 で追加された f-string 記法を使っており、
> 3.11 以下では `SyntaxError` になります。Ubuntu 22.04 の標準 Python は 3.10 なので、必ず仮想環境を使ってください。

---

## 2. 別の PC へのインストール

### 2-1. ゼロからインストールする (推奨)

`setup.sh` / `run_*.sh` / `tools/` / `tests/` / `requirements.lock.txt` / `llm.conf.example`
を新しい PC にコピーし、

```bash
cd <コピー先のフォルダ>
./setup.sh
```

これだけで以下がすべて自動で行われます。

1. `uv` が無ければ `~/.local/bin` に導入
2. `CommandGenerator` と **`Incheon2026`** (2026 世界大会の公式データ) を GitHub から clone (動作確認済みコミットに固定)
3. `.venv/` に Python 3.12 の仮想環境を作成し、`requirements.lock.txt` の固定バージョンで依存を導入
4. `Incheon2026` をコピーして `data/` を作成し、**後述のフォーマット不備を自動修正**
5. データを検証してサンプルコマンドを 3 個表示

最後にこう出れば成功です。

```
PROBLEMS: none
== done
```

最新の上流を使いたいときは `./setup.sh --latest`、テストも入れたいときは `./setup.sh --with-tests`。
`setup.sh` は何度実行しても安全で、既存の `data/` は上書きしません。

**別の大会のデータを使う場合**は `--competition=` で指定します。RoboCup@Home は大会ごとに
`github.com/RoboCupAtHome/<大会名>` というリポジトリを公開しています。

```bash
./setup.sh --competition=GermanOpen2026
./setup.sh --competition=Salvador2025          # 2025 世界大会 (練習用)
./setup.sh --competition=CompetitionTemplate   # 中身が汎用の空テンプレート
```

`data/` を作り直したいときは `rm -rf data` してから `./setup.sh` を実行してください。

### 2-2. フォルダごとコピーする場合 (会場でネットが無いとき)

このフォルダ全体を USB などでコピーします。ただし `.venv/` の中には
**絶対パスが埋め込まれている**ため、コピー先でそのままでは動きません。コピー後に

```bash
./setup.sh --recreate    # .venv を作り直す。data/ は既存のものが使われる
```

を実行してください。`CommandGenerator/` と `Incheon2026/` が既にあるので clone は走らず、
依存パッケージのダウンロードだけがネットを必要とします。完全オフラインで持ち込みたい場合は、
事前に会場で使う PC 上で一度 `./setup.sh` を通しておいてください。

### 2-3. uv を使わず手動で入れる

Python 3.12 が既にある場合:

```bash
git clone https://github.com/RoboCupAtHome/CommandGenerator.git
git clone https://github.com/RoboCupAtHome/Incheon2026.git
python3.12 -m venv .venv
./.venv/bin/pip install -r requirements.lock.txt
./.venv/bin/pip install -e ./CommandGenerator --no-deps
cp -r Incheon2026 data && rm -rf data/.git data/.gitmodules
python3 tools/fix_data_format.py data
```

---

## 3. 起動する

### GUI

```bash
./run_gpsr_ui.sh
```

起動すると

```
NiceGUI ready to go on http://localhost:8080, http://192.168.0.104:8080, ...
```

と出るので、ブラウザで `http://localhost:8080` を開きます。表示された LAN の URL を使えば、
**同じネットワークのタブレットやサブ PC からも開けます** (審判用の大画面に出すときに便利)。

よく使うオプション:

```bash
./run_gpsr_ui.sh --ui-port 9000          # ポートを変える (8080 が埋まっているとき)
./run_gpsr_ui.sh -d /path/to/other/data  # 別のアリーナデータを使う
./run_gpsr_ui.sh --ui-show               # 起動時にブラウザを自動で開く
```

停止は `Ctrl+C` です。

### CLI (テキスト版)

```bash
./run_cli.sh
```

数字を入力して Enter を押すと生成されます。

| 入力 | 内容 |
|---|---|
| `1` | 任意のコマンド |
| `2` | 物体操作を含まないコマンド (人に関するタスク) |
| `3` | 物体操作を含むコマンド |
| `4` | 3 個まとめて生成 |
| `5` | EGPSR のセットアップを生成 (個数を聞かれ、番号入力で個別に振り直し、`r` で全部振り直し) |
| `0` | 直前のコマンドを QR コードにして画像表示 |
| `q` | 終了 |

その他:

```bash
./run_cli.sh -p              # 読み込まれたアリーナデータを一覧表示
./run_cli.sh -g > out.txt    # 5000 個生成してデータの不備を洗い出す
```

> `0` (QR コード) は PIL が画像ビューアを起動します。デスクトップ環境が無い PC (SSH 越しなど) では表示できません。

---

## 4. GUI の使い方

### 生成画面 (`/`)

| 部品 | 役割 |
|---|---|
| `#` | 生成するコマンドの個数 (1〜5)。既定は 3 |
| **Generate GPSR Commands** | 指定した個数を生成する。1 個目は「人」系、2 個目は「物体」系、3 個目以降は任意カテゴリになり、最後にシャッフルされる |
| **Rephrase ALL** | 全コマンドを LLM で言い換える (LLM 設定が必要) |
| **New Command** | そのカードのコマンドだけ、同じカテゴリで作り直す |
| **Rephrase** | そのコマンドだけ言い換える |
| **Lock & Show** | 生成内容を確定し、提示用画面へ切り替える |

生成中・言い換え中はボタンが自動的に無効化されます。

### 提示画面 (`/task`)

- 上部のコマンドボタンを押すと、そのコマンドが下に大きく表示されます。
- **Text size** スライダー (32〜254 px) で文字サイズを変更できます。会場の距離に合わせて調整してください。
- **Phrasing 0 / 1 / 2 …** タブで、言い換え候補を切り替えられます (言い換えを実行した場合)。
- **Lock & Show** をもう一度押すと生成画面に戻ります。

### 記録

**Lock & Show** を押した瞬間に、その回のコマンドと言い換えがすべて `~/gpsr-ui.log` に記録されます。
競技後の確認や抗議対応に使えるので、大会中はこのファイルを消さないでください。

---

## 5. 大会データ (`data/`) の入れ方

`data/` には **2026 世界大会 (Incheon) の公式データ**が入っています。練習用に自分たちの
アリーナへ書き換えることもできます。ジェネレータが読むのは次の 4 ファイルだけです。

```
data/
├── names/names.md            人の名前
├── maps/room_names.md        部屋
├── maps/location_names.md    家具・設置場所とカテゴリ
└── objects/objects.md        物体とそのクラス
```

(`objects/known_objects/` 以下の画像や `maps/arena.png` はジェネレータは読みませんが、
チーム内資料として公式リポジトリの形式のまま置いておくと便利です)

### 5-1. `names/names.md`

```markdown
## Names
| Names |
| ------------ |
| Adel |
| Angel |
```

- 1 行 1 名前。
- **英字 1 単語のみ**。スペース・ハイフン・数字を含む名前 (`Mary Jane`, `Anne-Marie`, `Taro3`) は
  **エラーにならず黙って無視されます**。

### 5-2. `maps/room_names.md`

```markdown
## Rooms
| Name |
| ------------ |
| kitchen |
| living room |
```

- **英字 1〜2 単語まで**。3 単語以上 (`big living room`) やハイフン入りは無視されます。

### 5-3. `maps/location_names.md` ← ここが一番はまります

```markdown
## Locations
| Number | Name  | Object Category |
| ------------ | ----------- | ----------- |
| 1 | laundry table (p) | fabrics |
| 2 | washing machine (p) | |
| 10 | refrigerator | |
```

- `Name` に `(p)` を付けると「物を置ける場所 (placement location)」になります。
- `Object Category` は「その家具が既定の置き場所になっている物体クラス」。
  `objects.md` のクラス名 (複数形) と綴りを一致させてください。空欄で構いません。
- 名前に使えるのは**英字とスペースだけ**です。数字やハイフン (`table 2`, `side-table`) を入れると、
  その行だけでなく**前後の行まで巻き込んで読み飛ばされます**。

> **最重要**: 上流のパーサは 3 列目の後ろにも `|` があることを前提にしています。
> `| 1 | bed (p) |` のように行末の `|` が 1 本足りない行が混ざっていると、
> **その行だけでなく前後の行も巻き込んで読み飛ばされ、しかも警告が一切出ません**。
> 必ずすべての行を `| 番号 | 名前 | カテゴリ |` の形にしてください。直すには:
>
> ```bash
> python3 tools/fix_data_format.py data
> ```

#### 公式 2026 データにあった不備 (`data/` では修正済み)

`Incheon2026` をそのまま読ませると 2 つ問題が出たので、`data/` を作る際に自動で直しています。
`Incheon2026/` の方は公式のまま残してあるので、差分を見たいときはそちらと比べてください。

1. **全 20 行で行末の `|` が無い** — `fix_data_format.py` が補完します。
2. **13 行目で名前とカテゴリの間の `|` が抜けている** — 公式ファイルはこうなっています。

   ```markdown
   | 13 | cooking table (p) cleaning supplies |
   ```

   このままだと家具名が `cooking table cleaning supplies` という 1 個の場所として読まれます。
   `(p)` は必ず名前の終わりなので、そこで分割して次のように直しています。

   ```markdown
   | 13 | cooking table (p) | cleaning supplies |
   ```

3. **8 行目のカテゴリが `foods`** — `objects.md` のクラス名は `food` なので綴りが合いません。
   これは**未修正**です。GPSR の生成には影響しない (Storing Groceries 用の情報) ため公式のままにし、
   `check_data.py` が WARNING として毎回知らせます。

### 5-4. `objects/objects.md`

```markdown
# Class drinks (drink)

| Objectname               |  Image                   |
:-------------------------:|:-------------------------:
| coke | ![](known_objects/drinks!drink/coke.jpeg) |
| red_bull | ![](known_objects/drinks!drink/red_bull.jpeg) |
```

- クラスの見出しは `# Class 複数形 (単数形)` の形式。生成文中で `drinks` / `a drink` と使い分けられます。
- 物体名の `_` は表示時に半角スペースへ変換されます (`red_bull` → `red bull`)。
  **物体名にスペースを直接書かないでください。**
- `Image` 列は任意です (ジェネレータは無視します)。

### 5-5. 書き換えたら必ず検証する

```bash
./.venv/bin/python tools/check_data.py data
```

出力例:

```
ok names                  table rows:  10   parsed:  10
ok rooms                  table rows:   4   parsed:   4
ok locations              table rows:  20   parsed:  20
ok object categories      table rows:   8   parsed:   8
   objects: 30   placement locations: 14   storage categories: 8

PROBLEMS: none

WARNINGS (generation still works)
  - the 'Object Category' column of maps/location_names.md names ['foods'], ...
```

`PROBLEMS` は生成が壊れるもの、`WARNINGS` は知っておいた方がよいが生成は動くものです
(上の `foods` は公式データ由来のもので、そのままで構いません)。
表の書式を崩した場合はこう出ます。

```
!! locations              table rows:  20   parsed:  11

PROBLEMS
  - locations: 20 row(s) in the markdown table but 11 parsed
      a location name may only contain letters, spaces and the '(p)' marker, and every row must end with '|'
      try: python3 tools/fix_data_format.py data
```

`ok` は「表に書いた行数」と「実際に読み込めた数」が一致しているという意味です。
**`!!` が出たら必ず直してから本番に臨んでください。** 黙って項目が消えたまま競技が始まるのが一番危険です。

仕上げに、5000 個生成してクラッシュしないかも確認しておくと安心です。

```bash
./run_cli.sh -g > /dev/null && echo OK
```

---

## 6. LLM による言い換え (任意)

**Generate は LLM 無しで動きます。** LLM が必要なのは Rephrase / Rephrase ALL だけです。
接続先はジェネレータに内蔵されておらず、**PC ごとに自分で指定する必要があります**
(指定しないと `https://api.openai.com` に鍵無しで接続 → `LLM ERROR`)。

### 6-1. その PC で使える LLM を探す

```bash
./.venv/bin/python tools/check_llm.py
```

引数なしで実行すると、そのPCのローカルポート (Ollama 11434 / vLLM 8000 / LM Studio 1234 など) を
順に叩いて、見つかったサーバで**実際に言い換えを 1 回実行**します。成功すると、そのまま
`llm.conf` に貼れる行を出してくれます。

```
found Ollama on port 11434: gpsr-planner:latest, qwen3:8b, qwen2.5:7b-instruct

testing http://localhost:11434/v1/chat/completions  -a <set>  -m gpsr-planner:latest
  OK (4.0s for one command, 3 phrasings)
  in : Tell me what is the heaviest dish on the shelf
  out 0: What is the heaviest dish currently located on the shelf?
  out 1: Can you tell me which dish on the shelf is the heaviest?
  out 2: Which dish on the shelf weighs the most?

add this line to llm.conf:
  LLM_ARGS="--host localhost --port 11434 -a local -m gpsr-planner:latest"
```

失敗した場合も、原因と直し方 (モデル名が要る / thinking 非対応 / 鍵が違う / 誰も待ち受けていない)
を日本語ではありませんが具体的に出します。特定のサーバを直接試すこともできます。

```bash
./.venv/bin/python tools/check_llm.py --host 192.168.0.5 --port 11434 -a local -m qwen3:8b
./.venv/bin/python tools/check_llm.py -u https://api.openai.com/v1/chat/completions -a sk-... -m gpt-5
```

### 6-2. `llm.conf` に書いておく

LLM の設定は PC ごとに違うので、リポジトリではなく `llm.conf` に置きます。

```bash
cp llm.conf.example llm.conf
# check_llm.py が出した LLM_ARGS の行に書き換える
```

```bash
# llm.conf
LLM_ARGS="--host localhost --port 11434 -a local -m qwen3:8b"
```

以降は今までどおり起動するだけで、自動的に読み込まれます。

```bash
./run_gpsr_ui.sh
# → llm.conf: --host localhost --port 11434 -a local -m qwen3:8b
```

コマンドラインで LLM オプションを渡した場合はそちらが優先されます。
`llm.conf` は API キーを含みうるので `.gitignore` に入れてあります。

### 6-3. LLM が無い PC ではどうするか

`check_llm.py` が何も見つけられなかった場合、選択肢は 3 つです。

| 状況 | やること |
|---|---|
| その PC に入れてよい | `curl -fsSL https://ollama.com/install.sh \| sh` → `ollama pull qwen3:8b` → `check_llm.py` |
| チームの別 PC に LLM がある | その PC で LLM サーバを LAN に公開し、`--host <そのPCのIP> --port 11434` を指定 (Ollama は既定で `127.0.0.1` のみなので `OLLAMA_HOST=0.0.0.0` が必要) |
| 会場でネットが使える | OpenAI の鍵を使う: `LLM_ARGS="-a sk-xxxxxxxx -m gpt-5"` |

**どれも用意できなくても競技はできます。** Rephrase が使えないだけで、GPSR コマンドの生成・表示・
ログ記録はすべて動きます。

### 6-4. サーバ別の注意点

| サーバ | 注意 |
|---|---|
| Ollama | `-m` が**必須** (無いと `model is required`)。さらに **thinking 対応モデル**が必要で、`qwen2.5:7b-instruct` は `does not support thinking` で失敗します。`qwen3:8b` と `gpsr-planner:latest` は動作確認済み |
| vLLM | 起動時にモデルが 1 つに決まるので `-m` は不要。付けないと「思考なし」指定でリクエストされます |
| OpenAI | `--url`/`--host` を省くと自動的に `api.openai.com` + `gpt-5` になります |

`-a` (API キー) はローカルサーバでは中身を見られませんが、**省略はできません**。

### 6-5. 速度

言い換えは 1 コマンドにつき 3 通り生成されます。qwen3:8b で 1 コマンドあたり 10〜20 秒、
gpsr-planner で 4 秒ほどでした。**Rephrase ALL は 3 コマンド分まとめて走る**ので、
本番では必要なコマンドだけ個別に Rephrase する方が安全です。

LLM が Markdown の箇条書き以外を返すと上流のパーサが例外を投げ、GUI に `LLM ERROR` と出ます
(生成そのものは続行できます)。

---

## 7. ログ

`~/gpsr-ui.log` に追記されます。

- 生成したコマンド (`Generated command: ...`)
- **Lock & Show** を押した時点の確定内容 (`TASKS LOCKED` 以下)

---

## 8. トラブルシューティング

| 症状 | 原因と対処 |
|---|---|
| `ERROR: [Errno 98] Address already in use` | 8080 番が使用中。`./run_gpsr_ui.sh --ui-port 9000` で変更するか、前回のプロセスを終了 (`pkill -f gpsr_ui`) |
| `SyntaxError` が出る | Python 3.12 未満で動かしている。`.venv` を使わず `python3` で直接実行していないか確認 |
| ROS を source した端末で `ModuleNotFoundError` などが起きる | ROS の `PYTHONPATH` (Python 3.10 の site-packages) が仮想環境に混ざるため。`run_*.sh` は内部で `unset PYTHONPATH` しているので、**必ずスクリプト経由で起動**してください |
| コマンドに出てくる家具・部屋が明らかに少ない | データのフォーマット不備。5-5 の検証を実行 |
| `argument -d/--data-dir: '...' is not a valid path` | データフォルダのパスが違う。`-d` に正しいパスを渡す (既定は `./data`) |
| Rephrase で `LLM ERROR` と出る | ほとんどの場合 **LLM を指定せずに起動している**(OpenAI に鍵無しで接続 → 401)。`./.venv/bin/python tools/check_llm.py` で使える接続先を探し、`llm.conf` に書いてください。端末に出る例外も確認してください。生成自体は LLM 無しで続行できます |
| フォルダを移動・リネームしたら動かなくなった | `.venv` には**絶対パスが埋め込まれています**。移動先で `./setup.sh --recreate` を実行してください (`data/` と `llm.conf` はそのまま引き継がれます) |
| `athome-generator-gpsr-ui` を直接叩くと落ちる | 上流の既定データパスが開発者の環境のまま (`/media/mediassd/...`) なので、`-d` が必須。`run_gpsr_ui.sh` を使えば自動で付きます |
| ブラウザを別 PC から開けない | サーバは `0.0.0.0` で待ち受けています。ファイアウォールで 8080 番を許可してください |

動作確認をまとめて実行するには:

```bash
./run_tests.sh
```

データ検証と、GUI のボタン操作 (生成 → Lock & Show) の自動テストが走ります。
`3 passed` と出れば正常です。

---

## 9. ファイル構成

```
.
├── README_ja.md            この説明書
├── setup.sh                セットアップ (別 PC ではこれを実行)
├── run_gpsr_ui.sh          GUI 起動
├── run_cli.sh              CLI 起動
├── run_tests.sh            動作確認
├── requirements.lock.txt   動作確認済みの依存バージョン
├── llm.conf.example        LLM 設定のひな形 (コピーして llm.conf を作る)
├── llm.conf                ★ この PC の LLM 設定 (git 管理外)
├── tools/
│   ├── gpsr_ui.py          GUI ランチャ (ポート指定・自動リロード無効化)
│   ├── check_data.py       アリーナデータの検証
│   ├── check_llm.py        LLM 接続先の探索と疎通テスト
│   └── fix_data_format.py  location_names.md の行末 `|` を補う
├── tests/                  GUI の自動テスト
├── data/                   ★ 自分たちのアリーナデータ (ここを編集する)
├── CommandGenerator/       上流リポジトリ (触らない)
├── Incheon2026/            2026 世界大会の公式データ (触らない・data/ の元)
└── .venv/                  Python 3.12 仮想環境 (別 PC には持っていかない)
```

`tools/gpsr_ui.py` は上流のコードを一切書き換えずに、起動時の設定だけを差し替えるラッパです
(上流は `ui.run(show=False)` 決め打ちでポートが 8080 固定・自動リロード有効のため)。
上流を更新しても、この仕組みはそのまま使えます。

---

## 10. 更新する

```bash
./setup.sh --latest
```

上流の最新版を取得し直します。更新後は必ず

```bash
./run_tests.sh
```

で動作を確認してください。上流の変更で GUI が壊れた場合は、`setup.sh` の
`GEN_COMMIT` に書かれている動作確認済みコミットに戻せます (引数なしの `./setup.sh` がそれです)。
