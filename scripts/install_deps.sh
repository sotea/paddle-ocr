#!/usr/bin/env bash
set -euo pipefail

export PATH="$HOME/.local/bin:$PATH"
PROJ="$HOME/paddleocr"
PY="$PROJ/.venv/bin/python"
cd "$PROJ"

echo "=== [1/2] Installing paddlepaddle-gpu==3.2.1 (CUDA 12.6 build) ==="
uv pip install --python "$PY" \
    --index-strategy unsafe-best-match \
    --extra-index-url https://www.paddlepaddle.org.cn/packages/stable/cu126/ \
    "paddlepaddle-gpu==3.2.1"

echo "=== [2/2] Installing paddleocr[doc-parser] >= 3.6.0 ==="
uv pip install --python "$PY" -U "paddleocr[doc-parser]>=3.6.0"

echo "=== Installed key packages ==="
uv pip list --python "$PY" 2>/dev/null | grep -Ei "paddle|safetensors|transformers|opencv|numpy" || true
echo "DONE_INSTALL"
