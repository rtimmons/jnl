#!/usr/bin/env bash

set -eo pipefail

if [ ! -d "venv" ]; then
    brew install pyenv
    pyenv install -s
    pyenv rehash
    pip install virtualenv
    virtualenv venv
    source ./venv/bin/activate
    pip install -r requirements.txt
fi
