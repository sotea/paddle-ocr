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

# 出力先。環境変数 PADDLEOCR_OUTPUT_DIR で上書き可能。
# 既定はこのスクリプトと同じディレクトリ直下の output/（リポジトリ相対なので
# clone する場所に依存しない）。
DEFAULT_OUTPUT_DIR = str(Path(__file__).resolve().parent / "output")
OUTPUT_DIR = os.environ.get("PADDLEOCR_OUTPUT_DIR", DEFAULT_OUTPUT_DIR)


def main() -> None:
    input_path = sys.argv[1] if len(sys.argv) > 1 else DEMO_IMAGE
    log(f"入力: {input_path}")

    # 入力ファイル名(拡張子なし)のサブフォルダを output/ 配下に作り、そこへ保存する。
    # 複数ファイルを解析しても出力が混ざらないようにするため。
    # URL 入力でもパス末尾のファイル名から stem を取り出せる。
    stem = Path(input_path).stem
    out_dir = os.path.join(OUTPUT_DIR, stem)
    log(f"出力先: {out_dir}")
    Path(out_dir).mkdir(parents=True, exist_ok=True)

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

    # 1) ページ単位で Markdown / JSON を保存する。
    #    画像も含めて save_to_markdown 側が imgs/ 等へ書き出すため、
    #    結合版で画像参照を活かすにもこの保存が必要。
    markdown_list = []
    for res in results:
        res.save_to_json(save_path=out_dir)
        res.save_to_markdown(save_path=out_dir)
        # 結合用に各ページの markdown データ(テキスト+画像参照の dict)を集める
        markdown_list.append(res.markdown)

    # 2) 全ページを結合した 1 つの Markdown を追加で書き出す。
    #    ページをまたぐ表・段落を考慮するため、パイプライン提供の結合関数を使う。
    merged_md_path = os.path.join(out_dir, f"{stem}.md")
    markdown_texts = pipeline.concatenate_markdown_pages(markdown_list)
    # 環境によって戻り値が (テキスト, 画像dict) のタプルの場合があるため吸収する
    if isinstance(markdown_texts, tuple):
        markdown_texts = markdown_texts[0]
    with open(merged_md_path, "w", encoding="utf-8") as f:
        f.write(markdown_texts)
    log(f"結合 Markdown を保存: {merged_md_path}")

    log(
        f"[DONE] 解析完了。'{out_dir}' にページ単位の Markdown / JSON と "
        f"結合版 '{stem}.md' を保存しました。"
    )


if __name__ == "__main__":
    main()
