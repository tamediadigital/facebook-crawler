#!/bin/bash
set -eu
echo $CRAWLER_NAME
echo $CRAWL_TYPE
python3 -m playwright install chromium
python3 main.py
