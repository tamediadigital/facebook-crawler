#!/bin/bash
set -eu
echo $CRAWLER_NAME
echo $CRAWL_TYPE
echo $FILE_TO_EXECUTE
echo $DATE

if [ "$FILE_TO_EXECUTE" == "crawling" ]; then
    python3 -m playwright install firefox
    python main.py
else
    python deduplication.py
fi
