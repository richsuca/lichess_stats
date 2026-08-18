#!/usr/bin/env bash
set -euo pipefail

echo "=== ruff check ==="
./venv/bin/ruff check .

echo "=== ruff format ==="
./venv/bin/ruff format --check .

echo "=== mypy ==="
./venv/bin/mypy *.py

echo "=== typos ==="
~/.local/bin/typos .

echo "All checks passed."
