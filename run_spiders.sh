#!/bin/bash
set -eu

python3 -m playwright install firefox
python main.py
