#!/bin/zsh
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: ./scripts/run_r.sh path/to/script.R [args...]" >&2
  exit 1
fi

if command -v Rscript >/dev/null 2>&1; then
  Rscript --vanilla "$@"
  exit 0
fi

if conda run -n dl python -c 'import shutil, sys; sys.exit(0 if shutil.which("Rscript") else 1)' >/dev/null 2>&1; then
  conda run -n dl Rscript --vanilla "$@"
  exit 0
fi

echo "Rscript is not available in the dl environment or on the system PATH." >&2
echo "Preferred path:" >&2
echo "  ./scripts/setup_dl_runtime.sh" >&2
echo "Fallback path:" >&2
echo "  brew install r quarto" >&2
exit 1
