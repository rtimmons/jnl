#!/usr/bin/env bash

set -eo pipefail

if [[ ! -d "venv" || ! -e "venv/setup-done" ]]; then
    rm -rf venv
    if ! command -v pyenv; then
        if command -v brew; then
            brew install pyenv
        else
            echo "Don't know how to install pyenv without homebrew." >&2
        fi
    fi

    pyenv install -s
    pyenv rehash
    python3 -mvenv venv
    # shellcheck disable=SC1091
    source ./venv/bin/activate
    python3 -m pip install --upgrade pip setuptools wheel
    pip install -r requirements.txt
    pip install -e .
    touch venv/setup-done
fi
