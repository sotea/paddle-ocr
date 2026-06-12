#!/usr/bin/env bash
# Wrapper to run any python script inside the project venv with required libs.
# Usage: bash scripts/run.sh <python_file> [args...]
set -euo pipefail

PROJ="$HOME/paddleocr"
VENV="$PROJ/.venv"

export LD_LIBRARY_PATH="$PROJ/syslibs/lib:/usr/lib/wsl/lib:${LD_LIBRARY_PATH:-}"
# Keep model/cache downloads inside the project (WSL side, fast disk)
export HF_HOME="$PROJ/.cache/huggingface"
export PADDLE_PDX_CACHE_HOME="$PROJ/.cache/paddlex"

exec "$VENV/bin/python" "$@"
