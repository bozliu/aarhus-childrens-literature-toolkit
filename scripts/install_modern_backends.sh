#!/bin/zsh
set -euo pipefail

conda run -n dl pip install -r environment/python-backends.txt
conda run -n dl python -m pip install -e .
echo "Installed optional modern Python backends into the dl environment."
