# PaddleOCR-VL-1.6 ローカル実行環境（Windows + WSL2 + GPU）

PaddleOCR-VL-1.6 (0.9B) を使って、画像・PDF を **ページ全体まるごと Markdown / JSON 化**するためのローカル環境です。
高速化のため **vLLM 推論サーバ**を使用します（標準バックエンドは低速のため非推奨）。

## 動作確認済み環境

| 項目 | 内容 |
|---|---|
| OS | Windows 11 Pro + WSL2 (Ubuntu 24.04) |
| GPU | NVIDIA RTX 4060 Ti 16GB (Compute Capability 8.9) |
| CUDA Driver | 13.1（WSL内で GPU 認識済み） |
| Python | 3.12（`uv` 管理） |

> メモ: VLM 推論は vLLM(要 GPU, CC ≥ 8.0) を使用します。レイアウト検出は PaddlePaddle(GPU) 上で動きます。

## 構成（2 プロセス / 2 venv）

```
Windows 11
└─ WSL2 (Ubuntu 24.04)  ← GPU はここを通って利用
   ├─ ~/paddleocr/.venv        … OCR パイプライン (paddleocr + paddlepaddle-gpu)
   └─ ~/paddleocr/.venv-vllm   … vLLM 推論サーバ (torch + vllm + flash-attn)
```

- **vLLM サーバ**: VLM 本体を `http://127.0.0.1:8118/v1` で常駐サーブ
- **OCR パイプライン**: レイアウト検出 + サーバ呼び出しで結果を Markdown/JSON 化
- ソースコード・スクリプト・出力は Windows 側 `c:\projects\paddle-ocr`（WSL からは `/mnt/c/projects/paddle-ocr`）に配置。venv とモデルキャッシュは高速化のため WSL 側 `~/paddleocr` に配置。

---

## セットアップ手順（初回のみ）

> 以降の手順は、本リポジトリを Windows 側 `c:\projects\paddle-ocr`（WSL から `/mnt/c/projects/paddle-ocr`）に clone した前提で記載しています。別の場所に置いた場合は、各コマンド中のこのパスをご自身の clone 先に読み替えてください。

すべて WSL の bash で実行します。スクリプトは CRLF 改行のため、各スクリプトは事前に `sed -i 's/\r$//'` で LF 化してから実行してください（下記コマンドに含めています）。

### 0. 前提ツール

`uv`（Python パッケージ管理）を導入:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 1. システム依存（要 sudo・1 回だけ）

`gcc`（vLLM の Triton JIT が実行時に使用）と `libgomp`（PaddlePaddle の OpenMP ランタイム）を一括導入:

```bash
sudo apt update && sudo apt install -y build-essential
```

### 2. OCR パイプライン環境

```bash
cd /mnt/c/projects/paddle-ocr
sed -i 's/\r$//' scripts/setup_venv.sh scripts/install_deps.sh
bash scripts/setup_venv.sh     # ~/paddleocr/.venv を作成
bash scripts/install_deps.sh   # paddlepaddle-gpu 3.2.1 + paddleocr[doc-parser] 3.7.0
```

GPU 動作確認（任意）:

```bash
bash scripts/run.sh scripts/gpu_check.py
# => "PaddlePaddle works well on 1 GPU." が出れば OK
```

### 3. vLLM 推論サーバ環境（別 venv で依存競合を回避）

```bash
cd /mnt/c/projects/paddle-ocr
sed -i 's/\r$//' scripts/setup_vllm.sh scripts/setup_vllm2.sh scripts/install_flashattn.sh scripts/get_pyheaders.sh
bash scripts/setup_vllm.sh        # ~/paddleocr/.venv-vllm + paddlex 3.7.1
bash scripts/setup_vllm2.sh       # torch==2.8.0 + vllm==0.10.2 + xformers
bash scripts/install_flashattn.sh # flash-attn 2.8.3 (torch2.8/cp312/abiTRUE のプレビルトwheel)
bash scripts/get_pyheaders.sh     # Python 開発ヘッダを deb 展開 (sudo 不要・Triton 用)
```

---

## 使い方（日常運用）

### 1. vLLM サーバを起動（常駐。1 回起動すれば使い回せます）

```bash
cd /mnt/c/projects/paddle-ocr
sed -i 's/\r$//' scripts/run_server.sh scripts/run.sh
nohup bash scripts/run_server.sh 8118 > /tmp/vllm_server.log 2>&1 &
```

起動完了（約 40 秒）を確認:
- 約40秒後にサーバが立ち上がったかを確認します。/tmp/vllm_server.log を tail などで覗けば、起動の進捗やエラーもリアルタイムに追えます。
```bash
curl -s http://127.0.0.1:8118/v1/models
# => {"object":"list","data":[{"id":"PaddleOCR-VL-1.6-0.9B",...}]} が返れば OK
```

### 2. 画像・PDF を解析

```bash
# 引数なし: 公式デモ画像で動作確認
bash scripts/run.sh parse_doc.py

# 自分のファイル(Windows 上のファイルは /mnt/c/... で指定)
bash scripts/run.sh parse_doc.py /mnt/c/projects/paddle-ocr/sample.pdf
```

出力は既定でリポジトリ直下の `output/` に保存されます（環境変数 `PADDLEOCR_OUTPUT_DIR` で変更可能）。

- `<name>.md` … 見出し・段落・表・画像埋め込み付き Markdown
- `<name>_res.json` … 座標等を含む構造化 JSON
- `imgs/` … 切り出し画像

### 3. サーバを停止

```bash
pkill -f paddlex_genai_server
```

> サーバは WSL を閉じる/PC を再起動すると停止します。再開時は「1. サーバ起動」を実行してください。

---

## PowerShell から直接実行する場合

> **重要**: `wsl -e bash -lc "... &"` のように **バックグラウンド(`&`)で起動しない**でください。
> `wsl -e` のワンショット実行はコマンドが戻った時点で WSL セッションを手放すため、
> 直後に WSL ディストロごとシャットダウンし、起動したサーバも一緒に停止します
> （`/tmp` も初期化されログも残りません）。
> サーバは下記のように **専用ウィンドウで前面起動して常駐**させます。

```powershell
# (再起動時のみ) 既存サーバ・子プロセスが残っているとポート 8118 衝突で新規起動が即終了する。
# vLLM は APIServer 以外に EngineCore などの子プロセスも生成するため -9 で確実に止め、
# ポートが解放される(free になる)まで確認してから起動する。
wsl -e bash -lc "pkill -9 -f paddlex_genai_server; sleep 3; (ss -ltn 2>/dev/null | grep -q ':8118 ' && echo 'PORT 8118 STILL IN USE' || echo 'port 8118 free')"

# サーバ起動: 専用ウィンドウで前面起動し、ログも残す（このウィンドウは閉じないこと）
# 注意: -ArgumentList は「1 つの文字列」で渡し、bash へのコマンドは二重引用符で囲む。
# 配列（'-e','bash',...）で渡すと Windows PowerShell 5.1 はスペースを含む要素を
# 引用符で括らないため、bash -lc が受け取るスクリプトが先頭の cd だけになり即終了する。
Start-Process wsl -ArgumentList '-e bash -lc "cd /mnt/c/projects/paddle-ocr && bash scripts/run_server.sh 8118 2>&1 | tee /mnt/c/projects/paddle-ocr/vllm_server.log"'

# サーバ起動確認（約 40 秒後。モデル一覧が返れば OK）
wsl -e bash -lc "curl -s http://127.0.0.1:8118/v1/models"

# 解析実行
wsl -e bash -lc "cd /mnt/c/projects/paddle-ocr && bash scripts/run.sh parse_doc.py /mnt/c/projects/paddle-ocr/sample.pdf"

# サーバ停止（EngineCore などの子プロセスも残さないよう -9 で確実に止める）
wsl -e bash -lc "pkill -9 -f paddlex_genai_server"
```

> **起動ウィンドウが一瞬で消えてサーバが立ち上がらない場合**: `Start-Process` で開いた
> ウィンドウは中のプロセスが終了すると即閉じるため、原因が見えないまま一瞬で消えます。
> よくある原因は次の 2 つです。
>
> 1. **`-ArgumentList` の引数渡しミス（ログすら作られない場合はこれ）**:
>    `-ArgumentList '-e','bash','-lc','cd ... | tee ...'` のように **配列**で渡すと、
>    Windows PowerShell 5.1 はスペースを含む要素（bash コマンド文字列）を引用符で
>    括らずに wsl へ渡します。その結果 `bash -lc` が受け取るスクリプトが先頭の `cd` だけ
>    になり、bash はホームへ移動して即終了します。`tee` も走らないので `vllm_server.log`
>    すら作られません。上記コマンドのように **引数全体を 1 つの文字列**にし、bash への
>    コマンドを**二重引用符**で囲んでください。
> 2. **ポート 8118 が使用中（ログに衝突エラーが残る場合はこれ）**:
>    すでに別のサーバが動いている（前回の起動分が残っている等）と、新規プロセスが
>    衝突で即終了します。上記の `pkill -9 -f paddlex_genai_server` で既存プロセスを
>    止め、`port 8118 free` を確認してから起動し直してください。
>
> エラー内容は `vllm_server.log`（上記コマンドで Windows 側に出力）で確認できます。
> なお `Start-Process` 内で `> file 2>&1` リダイレクトにすると画面に何も出ないまま
> 消えて原因が分かりづらいため、上記では `tee` で**画面表示とログ保存を両立**しています。

---

## スクリプト一覧

| ファイル | 役割 | 分類 |
|---|---|---|
| `scripts/setup_venv.sh` | OCR 用 venv 作成（`~/paddleocr/.venv`） | 構築 |
| `scripts/install_deps.sh` | `paddlepaddle-gpu` + `paddleocr[doc-parser]` 導入 | 構築 |
| `scripts/gpu_check.py` | PaddlePaddle の GPU 動作確認 | 確認(任意) |
| `scripts/setup_vllm.sh` | vLLM 用 venv 作成 + `paddlex` 導入 | 構築 |
| `scripts/setup_vllm2.sh` | `torch` + `vllm` + `xformers` 導入 | 構築 |
| `scripts/install_flashattn.sh` | `flash-attn 2.8.3`（torch2.8 用 wheel）導入 | 構築 |
| `scripts/get_pyheaders.sh` | Python 開発ヘッダ展開（Triton JIT 用、sudo 不要） | 構築 |
| `scripts/run_server.sh` | vLLM 推論サーバ起動 | 実行 |
| `scripts/run.sh` | パイプライン実行ラッパー（venv + 環境変数設定） | 実行 |
| `parse_doc.py` | 解析本体（既定で vLLM サーバを使用） | 実行 |

---

## トラブルシュート / 設計メモ

- **標準バックエンドが極端に遅い**: PaddlePaddle 動的グラフでの自己回帰デコードは CPU ボトルネックになり、デモ 1 枚が 14 分でも完了しませんでした。本環境では vLLM サーバ経由（デモ 1 枚 **約 11 秒**）を既定にしています。`parse_doc.py` は環境変数 `PADDLEOCR_VLLM_URL` で接続先を切替可能（空文字にすると標準バックエンド）。
- **vLLM サーバ起動時に `Failed to find C compiler`**: vLLM は一部 GPU カーネル（PaddleOCR-VL のビジョンエンコーダ内 rotary embedding など）を **Triton** で動かし、Triton は実行時にカーネルを JIT コンパイルする際、ホスト用モジュール（`cuda_utils.c` 等）を **ホストの C コンパイラ（gcc）でビルド**します。WSL に gcc が無いと、エンジン初期化が次のエラーで失敗します。
  ```
  RuntimeError: Failed to find C compiler. Please specify via CC environment variable ...
  → subprocess.CalledProcessError: Command '['/usr/bin/gcc', '.../cuda_utils.c', ...]'
  ```
  対処: `sudo apt install -y build-essential`（gcc/g++/make/libc ヘッダ）。これは `libgomp1`（PaddlePaddle の OpenMP）も依存として入れるため、`import paddle` 時の `libgomp.so.1: cannot open shared object file` も同時に解消します。
- **flash-attn のバージョン**: `paddlex` が要求する `flash-attn 2.8.2` には torch2.8 用プレビルト wheel が無いため、ABI 互換の **2.8.3 (torch2.8/cp312/cxx11abiTRUE)** wheel を直接 URL 指定で導入しています（`nvcc` でのソースビルド回避）。`paddlex` のプラグイン判定はバージョン不問（import 可否のみ）のため問題ありません。
- **Triton JIT が `Python.h` を要求**: gcc 導入後の続きの問題。Triton のビルドが今度は `fatal error: Python.h: No such file or directory` を出します。`build-essential` には Python 開発ヘッダが含まれないため、`get_pyheaders.sh` で `libpython3.12-dev` を deb 展開し、`run_server.sh` の `CPATH` で参照しています（sudo 不要）。
- **GPU メモリ**: vLLM はデフォルトで GPU メモリの大部分を予約します。本環境では `gpu_memory_utilization=0.5`（約 8GB）で起動し、ディスプレイ使用分との競合を回避しています。
- **PowerShell から `wsl -e ... &` で起動するとサーバが即停止する**: `wsl -e bash -lc "... &"` はバックグラウンド起動した直後に `wsl -e` コマンドが終了し、WSL セッションを保持するプロセスが無くなります。すると WSL2 はアイドルタイムアウトで**ディストロごとシャットダウン**するため、常駐させたい vLLM サーバも一緒に停止します（`/tmp/vllm_server.log` も消え、後から `curl .../v1/models` が無応答・ログ無しになります）。対処: PowerShell からは `Start-Process wsl -ArgumentList '-e','bash','-lc','... bash scripts/run_server.sh 8118'` で**専用ウィンドウを開いて前面起動**し、そのウィンドウを開いたままにします。WSL の対話的ターミナル内であれば「使い方」の `nohup ... &` 方式でも常駐します（ターミナルを閉じない前提）。
- **`Start-Process` の起動ウィンドウが一瞬で消えてサーバが立ち上がらない**: `Start-Process` で開いたウィンドウは中のプロセスが終了すると即閉じます。前面起動の手順自体が正しくても**すでに別のサーバが動いていてポート 8118 が使用中**だと、vLLM が起動途中で `WARNING port 8118 is used by process ... paddlex_genai_server` を出して**自分から終了**し、エラーが見えないまま一瞬で消えます。注意したいのは、vLLM は `APIServer` 以外に `EngineCore` などの**子プロセス**も生成するため、`pkill -f paddlex_genai_server`（既定は SIGTERM）では子プロセスが残ってポート/GPU を掴み続けることがある点です。対処: `wsl -e bash -lc "pkill -9 -f paddlex_genai_server; sleep 3"` で確実に止め、`ss -ltn | grep ':8118 '` で**ポートが解放された**ことを確認してから起動し直す。エラーを確実に残すには、`Start-Process` 内で `... bash scripts/run_server.sh 8118 2>&1 | tee /mnt/c/projects/paddle-ocr/vllm_server.log` のように `tee` で画面表示とログ保存を両立させる（`> file 2>&1` だと画面に何も出ず消えて原因が分かりづらい）。
- **改行コード**: スクリプトは Windows 上で編集されるため CRLF になりがちです。実行前に `sed -i 's/\r$//'` で LF 化してください。

## モデル

- [PaddlePaddle/PaddleOCR-VL-1.6 (HuggingFace)](https://huggingface.co/PaddlePaddle/PaddleOCR-VL-1.6) — Apache-2.0
- パラメータ約 0.9B / 重み約 1.9GB。109+ 言語対応、テキスト・表・数式・チャート・印影の認識に対応。

## ライセンス

本リポジトリのコード・スクリプトは [MIT License](LICENSE) です。
利用する PaddleOCR-VL-1.6 モデルは Apache-2.0（上記リンク参照）で別途配布されています。
