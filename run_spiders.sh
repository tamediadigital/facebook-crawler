#!/bin/bash
set -eu
echo $CRAWLER_NAME
echo $CRAWL_TYPE
echo $FILE_TO_EXECUTE
echo $DATE

if [$FILE_TO_EXECUTE = "crawling"]
than
  python3 -m playwright install firefox
  python3 main.py
else
  python3 deduplication.py
