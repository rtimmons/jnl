#!/usr/bin/env bash

set -eo pipefail

if [[ ! -d "venv" || ! -e "venv/setup-done" ]]; then
    rm -rf venv
    brew install pyenv
    pyenv install -s
    pyenv rehash
    python3 -mvenv venv
    source ./venv/bin/activate
    python3 -m pip install --upgrade pip setuptools wheel
    pip install -r requirements.txt
    pip install -e .
    touch venv/setup-done
fi
