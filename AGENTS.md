# AGENTS.md

このリポジトリで作業する AI エージェント向けのガイドです。詳細なセットアップ・運用手順は `README.md` を参照してください。

## プロジェクト概要

PaddleOCR-VL-1.6 (0.9B) を使い、画像・PDF を **ページ全体まるごと Markdown / JSON 化**するローカル環境です。高速化のため **vLLM 推論サーバ**を使います（標準バックエンドは低速のため非推奨）。

- 対象環境: **Windows 11 + WSL2 (Ubuntu 24.04) + NVIDIA GPU**
- Python: 3.12（`uv` 管理）
- 推論コマンドは基本 **WSL の bash** 上で実行する

## 実行環境の前提（重要）

エージェントが最も誤りやすいポイントです。

- **2 プロセス / 2 venv 構成**:
  - `~/paddleocr/.venv` … OCR パイプライン (`paddleocr` + `paddlepaddle-gpu`)
  - `~/paddleocr/.venv-vllm` … vLLM 推論サーバ (`torch` + `vllm` + `flash-attn`)
- **venv とモデルキャッシュは WSL 側 `~/paddleocr` に置く**（このリポジトリ内には作らない）。ソース・スクリプト・出力のみ Windows 側 `c:\projects\paddle-ocr`（WSL からは `/mnt/c/projects/paddle-ocr`）。
- Python は常に `scripts/run.sh` 経由で起動する（venv・`LD_LIBRARY_PATH`・キャッシュ環境変数を設定するラッパー）。`python` を直接叩かない。

## よく使うコマンド

すべて WSL の bash で、リポジトリルート (`/mnt/c/projects/paddle-ocr`) から実行します。

```bash
# vLLM サーバ起動（常駐。約40秒で起動完了）
nohup bash scripts/run_server.sh 8118 > /tmp/vllm_server.log 2>&1 &

# 起動確認
curl -s http://127.0.0.1:8118/v1/models

# 解析実行（引数なし=公式デモ画像 / 引数あり=対象ファイル）
bash scripts/run.sh parse_doc.py
bash scripts/run.sh parse_doc.py /mnt/c/projects/paddle-ocr/sample.pdf

# サーバ停止
pkill -f paddlex_genai_server
```

出力は `output/` に保存されます（`<name>.md` / `<name>_res.json` / `imgs/`）。`output/` は生成物なのでコミットしません（`.gitignore` 済み）。

## コーディング規約・慣習

- **シェルスクリプトは LF 改行**。Windows 上で編集すると CRLF になりがちで実行に失敗するため、編集後は `sed -i 's/\r$//' <file>` で LF 化する。スクリプト冒頭は `set -euo pipefail`。
- Python はログを `parse_doc.py` の `log()`（タイムスタンプ付き `print`）に倣う。型ヒントを付ける。
- ユーザー向けの説明・ログ・コメントは **日本語**。コードコメントは「なぜそうしているか」を書き、自明な説明は避ける。
- 接続先などの設定は環境変数で上書き可能にする（例: `PADDLEOCR_VLLM_URL`、`HF_HOME`、`PADDLE_PDX_CACHE_HOME`）。
- パスは原則 WSL 視点（`/mnt/c/...`）で記述する。

## 注意事項

- 新しい依存を足すときは 2 つの venv のどちらに入れるべきか（OCR 側か vLLM 側か）を意識する。両者は依存競合を避けるため分離している。
- モデル重み・キャッシュ・大容量バイナリはコミットしない。
- `git config` の変更や破壊的な git 操作（force push 等）は行わない。コミットはユーザーから明示的に依頼された場合のみ行う。
