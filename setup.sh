#!/usr/bin/env bash

set -eo pipefail

if [ ! -d "venv" ]; then
    pyenv install -s
    pyenv rehash
    pip install virtualenv
    virtualenv venv
    source ./venv/bin/activate
        pip install -r requirements.txt
    deactivate
fi

source ./venv/bin/activate
python ./setup.py develop
