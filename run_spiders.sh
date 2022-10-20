#!/bin/bash
set -eu
echo $DATE


python3 -m playwright install firefox
python main.py
