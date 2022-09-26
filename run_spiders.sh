#!/bin/bash
set -eu
echo $CRAWLER_NAME
echo $CRAWL_TYPE
echo $FILE_TO_EXECUTE
echo $DATE

if [ "$FILE_TO_EXECUTE" == "crawling" ]; then
    python3 -m playwright install firefox
    python main.py
elif [ "$FILE_TO_EXECUTE" == "delta" ]; then
    python delta.py
elif [ "$FILE_TO_EXECUTE" == "pagination" ]; then
    python3 -m playwright install firefox
    python pagination.py
elif [ "$FILE_TO_EXECUTE" == "base_items_crawler" ]; then
    python3 -m playwright install firefox
    python base_items_crawler.py
elif [ "$FILE_TO_EXECUTE" == "data_processing" ]; then
    python data_processing.py
else
    python deduplication.py
fi
