#!/bin/zsh
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: ./scripts/run_entrypoint.sh {legacy|modern|readme|report}" >&2
  exit 1
fi

mode="$1"

has_rscript() {
  if command -v Rscript >/dev/null 2>&1; then
    return 0
  fi
  conda run -n dl python -c 'import shutil, sys; sys.exit(0 if shutil.which("Rscript") else 1)' >/dev/null 2>&1
}

run_python() {
  case "$mode" in
    legacy) conda run -n dl python -m childlit_toolkit legacy ;;
    modern) conda run -n dl python -m childlit_toolkit modern ;;
    readme) conda run -n dl python -m childlit_toolkit render ;;
    report) conda run -n dl python -m childlit_toolkit report ;;
    *)
      echo "Unknown mode: $mode" >&2
      exit 1
      ;;
  esac
}

run_r() {
  case "$mode" in
    legacy) ./scripts/run_r.sh scripts/run_targets.R legacy ;;
    modern) ./scripts/run_r.sh scripts/run_targets.R modern ;;
    readme) ./scripts/run_r.sh scripts/render_readme.R ;;
    report) ./scripts/run_r.sh scripts/render_report.R ;;
    *)
      echo "Unknown mode: $mode" >&2
      exit 1
      ;;
  esac
}

if has_rscript; then
  run_r
else
  run_python
fi
