#!/usr/bin/env bash
# Set up the RoboCup@Home 2026 GPSR command generator on this machine.
# Safe to re-run: existing checkouts are updated, existing data is left alone.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

# A sourced ROS setup.bash puts its Python 3.10 site-packages on PYTHONPATH,
# which leaks into the 3.12 virtualenv and breaks imports.
unset PYTHONPATH

GEN_REPO="https://github.com/RoboCupAtHome/CommandGenerator.git"
# The arena data of one competition.  RoboCup@Home publishes one repository per
# event under github.com/RoboCupAtHome - Incheon2026 is the 2026 world
# championship.  Override with --competition NAME (e.g. GermanOpen2026).
COMPETITION="Incheon2026"
# Revisions verified to work together.  Use --latest to track the upstream tip.
GEN_COMMIT="fa8b9adf52c876042b81b7dbfd0e50fc00ef5cc6"
DATA_COMMIT="993bb7015566b8c943cd379db781257cbd6ff81b"
PYTHON_VERSION="3.12"

USE_LATEST=0
WITH_TESTS=0
RECREATE=0
for arg in "$@"; do
    case "$arg" in
        --latest)     USE_LATEST=1 ;;
        --with-tests) WITH_TESTS=1 ;;
        --recreate)   RECREATE=1 ;;
        --competition=*) COMPETITION="${arg#*=}"; DATA_COMMIT="" ;;
        -h|--help)
            sed -n '2,4p' "$0"
            echo
            echo "Options:"
            echo "  --latest      use the current upstream tip instead of the pinned revisions"
            echo "  --with-tests  also install pytest so ./run_tests.sh can run"
            echo "  --recreate    delete and rebuild .venv (needed after moving this folder)"
            echo "  --competition=NAME"
            echo "                arena data repository under github.com/RoboCupAtHome"
            echo "                (default: ${COMPETITION})"
            exit 0 ;;
        *)  echo "unknown option: $arg" >&2; exit 2 ;;
    esac
done

say() { printf '\n== %s\n' "$1"; }

# ---------------------------------------------------------------- 1. uv / python
say "checking the build front end"
UV=""
if command -v uv >/dev/null 2>&1; then
    UV="$(command -v uv)"
elif [ -x "$HOME/.local/bin/uv" ]; then
    UV="$HOME/.local/bin/uv"
else
    echo "uv not found, downloading it to ~/.local/bin"
    mkdir -p "$HOME/.local/bin"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    UV="$HOME/.local/bin/uv"
fi
if [ ! -x "$UV" ]; then
    echo "ERROR: could not install uv. Install it manually (https://docs.astral.sh/uv)" >&2
    echo "       or create the virtualenv yourself with a Python ${PYTHON_VERSION} interpreter." >&2
    exit 1
fi
echo "uv: $UV ($("$UV" --version))"

# ---------------------------------------------------------------- 2. sources
clone_or_update() {
    local dir="$1" url="$2" commit="$3"
    if [ ! -d "$dir/.git" ]; then
        say "cloning $url"
        git clone "$url" "$dir"
    else
        say "updating $dir"
        git -C "$dir" fetch --all --quiet || echo "  (offline - keeping the local checkout)"
    fi
    if [ "$USE_LATEST" -eq 1 ]; then
        git -C "$dir" checkout master --quiet 2>/dev/null || true
        git -C "$dir" pull --quiet 2>/dev/null || true
    else
        git -C "$dir" checkout --quiet "$commit" 2>/dev/null \
            || echo "  (could not check out $commit - keeping the current revision)"
    fi
    echo "  $dir @ $(git -C "$dir" rev-parse --short HEAD)"
}

clone_or_update CommandGenerator "$GEN_REPO" "$GEN_COMMIT"
clone_or_update "$COMPETITION" "https://github.com/RoboCupAtHome/${COMPETITION}.git" "$DATA_COMMIT"

# The two checkouts above are repositories of their own and must not be added to
# this one.  .gitignore covers the defaults; --competition=NAME is listed here so
# that it works for any event without editing a tracked file.
GIT_DIR_PATH="$(git -C "$ROOT" rev-parse --absolute-git-dir 2>/dev/null || true)"
if [ -n "$GIT_DIR_PATH" ]; then
    mkdir -p "$GIT_DIR_PATH/info"
    for d in CommandGenerator "$COMPETITION"; do
        grep -qxF "/$d/" "$GIT_DIR_PATH/info/exclude" 2>/dev/null \
            || echo "/$d/" >> "$GIT_DIR_PATH/info/exclude"
    done
fi

# ---------------------------------------------------------------- 3. virtualenv
say "creating the virtualenv (.venv, Python ${PYTHON_VERSION})"
# A virtualenv stores absolute paths, so one copied or moved from elsewhere is
# broken and has to be rebuilt.
if [ "$RECREATE" -eq 1 ]; then
    rm -rf "$ROOT/.venv"
fi
if [ -d "$ROOT/.venv" ] && [ ! -x "$ROOT/.venv/bin/python" ]; then
    echo ".venv looks broken - rebuilding it"
    rm -rf "$ROOT/.venv"
fi
if [ -d "$ROOT/.venv" ]; then
    echo "reusing the existing .venv (pass --recreate to rebuild it)"
else
    "$UV" venv --python "$PYTHON_VERSION" "$ROOT/.venv"
fi

say "installing dependencies"
export VIRTUAL_ENV="$ROOT/.venv"
if [ -f "$ROOT/requirements.lock.txt" ]; then
    "$UV" pip install -r "$ROOT/requirements.lock.txt"
    "$UV" pip install -e "$ROOT/CommandGenerator" --no-deps
else
    "$UV" pip install -e "$ROOT/CommandGenerator"
fi
[ "$WITH_TESTS" -eq 1 ] && "$UV" pip install pytest pytest-asyncio

# ---------------------------------------------------------------- 4. arena data
say "preparing the arena data (data/)"
if [ -d "$ROOT/data" ]; then
    echo "data/ already exists - left untouched"
    echo "  (to start over from ${COMPETITION}: rm -rf data && ./setup.sh)"
else
    cp -r "$ROOT/$COMPETITION" "$ROOT/data"
    rm -rf "$ROOT/data/.git" "$ROOT/data/.gitmodules"
    find "$ROOT/data" -name .DS_Store -delete
    python3 "$ROOT/tools/fix_data_format.py" "$ROOT/data"
    rm -f "$ROOT/data/maps/location_names.md.bak"
    echo "data/ created from ${COMPETITION}"
fi

# ---------------------------------------------------------------- 5. verify
say "verifying"
# A data problem should be reported loudly but must not abort the setup.
if ! "$ROOT/.venv/bin/python" "$ROOT/tools/check_data.py" "$ROOT/data" -n 3; then
    echo
    echo "!! the arena data has problems - see above before using the generator"
fi

say "LLM for the 'Rephrase' button (optional)"
if [ -f "$ROOT/llm.conf" ]; then
    echo "llm.conf found - the GUI will use it"
else
    echo "no llm.conf on this machine. Command generation works without one;"
    echo "only 'Rephrase' needs an LLM. To set it up here:"
    echo "  ./.venv/bin/python tools/check_llm.py     # finds and tests a server"
    echo "  cp llm.conf.example llm.conf              # then paste the line it prints"
fi

cat <<'MSG'

== done

  ./run_gpsr_ui.sh          start the GUI  -> http://localhost:8080
  ./run_cli.sh              start the text generator
  ./run_tests.sh            check that everything works

MSG
