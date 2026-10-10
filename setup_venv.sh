#!/bin/sh
# Create the project virtual environment at ~/.venvs/url-list and install deps.
set -eu

VENV="$HOME/.venvs/url-list"
ROOT="$(cd "$(dirname "$0")" && pwd)"
PYTHON="${PYTHON:-python3}"
if ! "$PYTHON" --version >/dev/null 2>&1; then
  for cand in /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
    if "$cand" --version >/dev/null 2>&1; then PYTHON="$cand"; break; fi
  done
fi

"$PYTHON" -m venv "$VENV"
"$VENV/bin/pip" install --upgrade pip
"$VENV/bin/pip" install -r "$ROOT/requirements.txt"

echo "Virtual environment ready: $VENV"
echo "Activate with: source $VENV/bin/activate"
