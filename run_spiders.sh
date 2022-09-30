#!/bin/bash
set -eu
echo $FILE_TO_EXECUTE
echo $DATE

python3 -m playwright install firefox
python main.py
