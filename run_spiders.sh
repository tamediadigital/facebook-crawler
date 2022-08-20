#!/bin/bash
set -eu
echo $CRAWLER_NAME
echo $CRAWL_TYPE
python3 -m playwright install firefox
python3 main.py
