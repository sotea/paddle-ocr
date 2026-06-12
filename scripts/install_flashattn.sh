#!/usr/bin/env bash
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
PY="$HOME/paddleocr/.venv-vllm/bin/python"

WHL="https://github.com/Dao-AILab/flash-attention/releases/download/v2.8.3/flash_attn-2.8.3%2Bcu12torch2.8cxx11abiTRUE-cp312-cp312-linux_x86_64.whl"

echo "=== Installing prebuilt flash-attn 2.8.3 (built for torch2.8, abiTRUE) ==="
uv pip install --python "$PY" --reinstall-package flash-attn "$WHL"

echo "=== Verify imports ==="
"$PY" -c "import flash_attn, xformers, torch, vllm; print('flash_attn', flash_attn.__version__); print('xformers', xformers.__version__); print('vllm', vllm.__version__); print('torch', torch.__version__)"
echo "FLASHATTN_DONE"
