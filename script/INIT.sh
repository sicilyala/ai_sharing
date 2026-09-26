#!/usr/bin/env bash
set -euo pipefail

# Standard repository startup and verification.
# Usage:
#   cd $(git rev-parse --show-toplevel) && ./script/INIT.sh

echo "=== Repository ==="
echo "Repo root: $(git rev-parse --show-toplevel)"
echo "Branch: $(git branch --show-current 2>/dev/null || echo unknown)"

cd "$(git rev-parse --show-toplevel)"
echo "pwd: $(pwd)"

echo
echo "=== Git working tree summary ==="
git status --short

echo
echo "=== uv ==="
if command -v uv >/dev/null 2>&1; then
	uv --version
else
	echo "uv not found on PATH; stopped"
	exit 1
fi

echo
echo "=== Python environment ==="
if [[ -f ".venv/bin/activate" ]]; then
	source ".venv/bin/activate"
	uv sync --frozen
	echo "OK: Python environment is activated and dependencies are installed"
	python --version
else
	echo "Missing .venv/bin/activate" >&2
	exit 1
fi

echo
echo "=== Ruff ==="
if python -m ruff --version >/dev/null 2>&1; then
	python -m ruff check
else
	echo "ruff unavailable in current environment; stopped"
	echo "Install with: uv add --dev ruff"
	exit 1
fi

echo
echo "=== mypy ==="
if python -m mypy --version >/dev/null 2>&1; then
	python -m mypy
else
	echo "mypy unavailable in current environment; stopped"
	echo "Install with: uv add --dev mypy"
	exit 1
fi

echo
echo "=== Pytest ==="
if find test -type f -name 'test_*.py' | grep -q .; then
	SDL_VIDEODRIVER="${SDL_VIDEODRIVER:-offscreen}" python -m pytest
else
	echo "No pytest files found; skipped"
fi

echo

echo
echo "=== ✅ Initial verification completes successfully! ==="
