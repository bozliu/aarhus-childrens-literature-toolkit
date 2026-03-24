#!/bin/zsh
set -euo pipefail

if conda run -n dl Rscript --version >/dev/null 2>&1; then
  echo "Rscript is already available inside the dl runtime path."
  exit 0
fi

if command -v mamba >/dev/null 2>&1; then
  mamba env update -n dl -f environment/dl-r-overlay.yml
else
  conda env update -n dl -f environment/dl-r-overlay.yml
fi
echo "Applied R/runtime overlay to the dl environment."
