#!/usr/bin/env bash
set -euo pipefail

export PATH="$HOME/.local/bin:$PATH"
PROJ="$HOME/paddleocr"
VENV="$PROJ/.venv-vllm"
cd "$PROJ"

echo "=== Creating vLLM venv (Python 3.12) ==="
uv venv --python 3.12 "$VENV"
PY="$VENV/bin/python"

echo "=== Installing paddlex + light deps (no paddlepaddle) ==="
uv pip install --python "$PY" "paddlex==3.7.1" "transformers<5.0.0" einops uvloop

echo "=== Installed so far (check for paddlepaddle) ==="
uv pip list --python "$PY" 2>/dev/null | grep -iE "paddle|transformers|torch|numpy" || true
echo "PART1_DONE"
