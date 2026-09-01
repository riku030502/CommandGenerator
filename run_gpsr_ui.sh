#!/usr/bin/env bash
# Start the GPSR web interface.  Open http://localhost:8080 in a browser.
#
#   ./run_gpsr_ui.sh                                  arena data from ./data
#   ./run_gpsr_ui.sh -d /path/to/other/data           different arena data
#   ./run_gpsr_ui.sh --ui-port 9000                   different web port
#   ./run_gpsr_ui.sh --host 192.168.0.5 --port 9090 -a KEY -m MODEL
#                                                     LLM for 'Rephrase'
#
# The LLM settings differ per machine, so they live in llm.conf (see
# llm.conf.example).  If that file exists its LLM_ARGS are added automatically;
# passing LLM options on the command line overrides it.  Find the right values
# with:  ./.venv/bin/python tools/check_llm.py
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
unset PYTHONPATH   # keep a sourced ROS environment out of the 3.12 virtualenv

if [ ! -x "$ROOT/.venv/bin/python" ]; then
    echo "ERROR: .venv is missing. Run ./setup.sh first." >&2
    exit 1
fi

args=("$@")

# arena data
case " $* " in
    *" -d "*|*" --data-dir "*) ;;
    *) args=(-d "${GPSR_DATA_DIR:-$ROOT/data}" "${args[@]+"${args[@]}"}") ;;
esac

# LLM settings from llm.conf, unless given on the command line
case " $* " in
    *" -u "*|*" --url "*|*" --host "*|*" -a "*|*" --api-key "*) ;;
    *)
        if [ -f "$ROOT/llm.conf" ]; then
            # shellcheck disable=SC1091
            . "$ROOT/llm.conf"
            if [ -n "${LLM_ARGS:-}" ]; then
                read -ra llm_extra <<< "$LLM_ARGS"
                args+=("${llm_extra[@]}")
                echo "llm.conf: $LLM_ARGS"
            fi
        fi
        ;;
esac

exec "$ROOT/.venv/bin/python" "$ROOT/tools/gpsr_ui.py" "${args[@]}"
