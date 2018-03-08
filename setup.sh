#!/usr/bin/env bash

set -eo pipefail

if [ ! -d "venv" ]; then
    pip install virtualenv
    virtualenv venv
    source ./venv/bin/activate
    pip install -r requirements.txt
fi
