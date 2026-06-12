#!/usr/bin/env bash
set -euo pipefail

export PATH="$HOME/.local/bin:$PATH"
PROJ="$HOME/paddleocr"
VENV="$PROJ/.venv-vllm"
PY="$VENV/bin/python"
cd "$PROJ"

echo "=== Installing torch==2.8.0 + vllm==0.10.2 + xformers ==="
uv pip install --python "$PY" "torch==2.8.0" "vllm==0.10.2" xformers

echo "=== torch ABI / cuda check ==="
"$PY" - <<'PYEOF'
import torch
print("torch", torch.__version__)
print("cuda available", torch.cuda.is_available())
print("cxx11_abi", torch._C._GLIBCXX_USE_CXX11_ABI)
print("cuda ver", torch.version.cuda)
print("py_tag", "cp312")
PYEOF
echo "PART2_DONE"
