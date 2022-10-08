#!/bin/bash
set -eu
echo $DATE


if [ "$FILE_TO_EXECUTE" == "main" ]; then
    python3 -m playwright install firefox
    python main.py
else
    python3 -m playwright install firefox
    python pagination.py
fi