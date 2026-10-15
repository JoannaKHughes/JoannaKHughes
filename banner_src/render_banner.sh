#!/bin/bash
# Render banner.html to assets/banner.png at 2x (3168x792) with headless Chrome.
set -euo pipefail
cd "$(dirname "$0")/.."
google-chrome --headless --disable-gpu --hide-scrollbars --force-device-scale-factor=2 \
  --window-size=1584,396 --virtual-time-budget=8000 \
  --screenshot="${1:-assets/banner.png}" "file://$PWD/banner_src/banner.html" 2>/dev/null
echo "wrote ${1:-assets/banner.png}"
