#!/usr/bin/env bash
set -uo pipefail
LIBDIR="$HOME/paddleocr/syslibs"
mkdir -p "$LIBDIR"
cd "$LIBDIR"

echo "=== Downloading libpython3.12-dev (no sudo) ==="
apt-get download libpython3.12-dev python3.12-dev 2>err2.log || { echo "download failed"; cat err2.log; }

ls -1 *.deb 2>/dev/null

echo "=== Extracting debs ==="
rm -rf pydev
mkdir -p pydev
for d in libpython3.12-dev_*.deb python3.12-dev_*.deb; do
  [ -f "$d" ] && dpkg-deb -x "$d" pydev && echo "extracted $d"
done

echo "=== Locate Python.h and pyconfig.h ==="
find pydev -name 'Python.h' 2>/dev/null
find pydev -name 'pyconfig.h' 2>/dev/null
echo "PYHEADERS_DONE"
