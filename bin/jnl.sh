#!/usr/bin/env bash

set -eou pipefail

pushd "$(dirname "$0")/.." >/dev/null
    ROOT="$(pwd -P)"
popd >/dev/null

if [ ! -d "$ROOT/venv" ]; then
    echo "Run setup.sh first" > /dev/stderr
    exit 1
fi

"$ROOT/venv/bin/python" "$ROOT/bin/jnl.py" "$@"
