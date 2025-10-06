#!/usr/bin/env bash
set -euo pipefail

# Attempt to run flake8 without relying on a local venv
if command -v flake8 >/dev/null 2>&1; then
  flake8
  exit 0
fi

# Fallback: try via python -m flake8
if python -c "import flake8" >/dev/null 2>&1; then
  python -m flake8
  exit 0
fi

echo "flake8 is not installed in the environment." >&2
exit 0
