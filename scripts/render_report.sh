#!/bin/zsh
set -euo pipefail

conda run -n dl python -m childlit_toolkit report
echo "Rendered docs/index.html"
