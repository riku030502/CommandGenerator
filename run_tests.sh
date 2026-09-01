#!/usr/bin/env bash
# Smoke-test the installation: validate the arena data, then drive the web
# interface's buttons through NiceGUI's user simulation.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
unset PYTHONPATH

if [ ! -x "$ROOT/.venv/bin/python" ]; then
    echo "ERROR: .venv is missing. Run ./setup.sh first." >&2
    exit 1
fi

if ! "$ROOT/.venv/bin/python" -c "import pytest, pytest_asyncio" 2>/dev/null; then
    echo "installing pytest into .venv"
    VIRTUAL_ENV="$ROOT/.venv" uv pip install pytest pytest-asyncio
fi

export GPSR_DATA_DIR="${GPSR_DATA_DIR:-$ROOT/data}"

echo "== data"
"$ROOT/.venv/bin/python" "$ROOT/tools/check_data.py" "$GPSR_DATA_DIR" -n 0

echo
echo "== web interface"
cd "$ROOT/tests"
exec "$ROOT/.venv/bin/python" -m pytest -q "$@"
