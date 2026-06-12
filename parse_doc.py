"""PaddleOCR-VL-1.6 でページ全体を解析し Markdown / JSON に出力するスクリプト.

使い方 (WSL内, リポジトリの run.sh 経由を推奨):
    bash scripts/run.sh parse_doc.py                 # 公式デモ画像で動作確認
    bash scripts/run.sh parse_doc.py path/to/file    # 画像/PDF を指定
"""

import os
import sys
import time
from pathlib import Path

from paddleocr import PaddleOCRVL

# vLLM サーバの URL（環境変数で上書き可能）。空文字にすると標準(低速)バックエンドを使用。
VLLM_SERVER_URL = os.environ.get("PADDLEOCR_VLLM_URL", "http://127.0.0.1:8118/v1")


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

DEMO_IMAGE = (
    "https://paddle-model-ecology.bj.bcebos.com/"
    "paddlex/imgs/demo_image/paddleocr_vl_demo.png"
)

# 出力は Windows 側のプロジェクトフォルダに保存し、Cursor から見えるようにする
OUTPUT_DIR = "/mnt/c/projects/paddle-ocr/output"


def main() -> None:
    input_path = sys.argv[1] if len(sys.argv) > 1 else DEMO_IMAGE
    log(f"入力: {input_path}")
    log(f"出力先: {OUTPUT_DIR}")
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    # 初回はモデル(PaddleOCR-VL-1.6 など)を自動ダウンロードするため時間がかかります
    log("パイプライン初期化(モデルロード)開始 ...")
    t0 = time.time()
    if VLLM_SERVER_URL:
        log(f"VLM 認識バックエンド: vllm-server ({VLLM_SERVER_URL})")
        pipeline = PaddleOCRVL(
            pipeline_version="v1.6",
            device="gpu:0",
            vl_rec_backend="vllm-server",
            vl_rec_server_url=VLLM_SERVER_URL,
        )
    else:
        log("VLM 認識バックエンド: native (低速)")
        pipeline = PaddleOCRVL(pipeline_version="v1.6", device="gpu:0")
    log(f"パイプライン初期化 完了 ({time.time() - t0:.1f}s)")

    log("推論(predict)開始 ...")
    t1 = time.time()
    output = pipeline.predict(input_path)
    results = list(output)
    log(f"推論 完了 ({time.time() - t1:.1f}s)")

    for res in results:
        res.save_to_json(save_path=OUTPUT_DIR)
        res.save_to_markdown(save_path=OUTPUT_DIR)

    log(f"[DONE] 解析完了。'{OUTPUT_DIR}' に Markdown / JSON を保存しました。")


if __name__ == "__main__":
    main()
