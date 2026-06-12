#!/usr/bin/env bash
set -euo pipefail

export PATH="$HOME/.local/bin:$PATH"

PROJ="$HOME/paddleocr"
mkdir -p "$PROJ"
cd "$PROJ"

echo "=== Creating venv with uv (Python 3.12) ==="
uv venv --python 3.12 .venv

echo "=== venv python version ==="
"$PROJ/.venv/bin/python" --version
echo "VENV_PATH=$PROJ/.venv"
