#!/usr/bin/env bash
# PaddleOCR-VL-1.6 を vLLM バックエンドでサーブする GenAI サーバを起動する。
set -euo pipefail

PROJ="$HOME/paddleocr"
export LD_LIBRARY_PATH="$PROJ/syslibs/lib:/usr/lib/wsl/lib:${LD_LIBRARY_PATH:-}"
# Triton の実行時 JIT が gcc で Python.h を見つけられるよう、展開した開発ヘッダを通す
PYINC="$PROJ/syslibs/pydev/usr/include"
# $PYINC 自体も含めることで pyconfig.h の <x86_64-linux-gnu/python3.12/pyconfig.h> を解決
export CPATH="$PYINC/python3.12:$PYINC:$PYINC/x86_64-linux-gnu/python3.12:${CPATH:-}"
export C_INCLUDE_PATH="$CPATH"
# 既にダウンロード済みのモデルキャッシュを再利用する
export PADDLE_PDX_CACHE_HOME="$PROJ/.cache/paddlex"
export HF_HOME="$PROJ/.cache/huggingface"

PORT="${1:-8118}"

exec "$PROJ/.venv-vllm/bin/paddlex_genai_server" \
    --model_name PaddleOCR-VL-1.6-0.9B \
    --backend vllm \
    --host 127.0.0.1 \
    --port "$PORT"
