#!/usr/bin/env bash
# Start the text-mode command generator (menu: 1-5 to generate, 0 for a QR code,
# q to quit).
#
#   ./run_cli.sh                    interactive generator on ./data
#   ./run_cli.sh -p                 print the parsed arena data and exit
#   ./run_cli.sh -g > out.txt       generate 5000 commands (data sanity check)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
unset PYTHONPATH

if [ ! -x "$ROOT/.venv/bin/athome-generator" ]; then
    echo "ERROR: .venv is missing. Run ./setup.sh first." >&2
    exit 1
fi

args=("$@")
case " $* " in
    *" -d "*|*" --data-dir "*) ;;
    *) args=(-d "${GPSR_DATA_DIR:-$ROOT/data}" "${args[@]+"${args[@]}"}") ;;
esac

exec "$ROOT/.venv/bin/athome-generator" "${args[@]}"
