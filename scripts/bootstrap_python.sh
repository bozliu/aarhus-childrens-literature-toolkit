#!/bin/zsh
set -euo pipefail

conda run -n dl python -m pip install --upgrade pip
conda run -n dl python -m pip install -r environment/python-core.txt
conda run -n dl python -m pip install -e .
echo "Bootstrapped Python dependencies and installed childlit_toolkit."
