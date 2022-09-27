#!/bin/bash
set -eu
echo $FILE_TO_EXECUTE
echo $DATE


if [ "$FILE_TO_EXECUTE" == "pagination" ]; then
    python pagination.py
elif [ "$FILE_TO_EXECUTE" == "base_items_crawler" ]; then
    python base_items_crawler.py
elif [ "$FILE_TO_EXECUTE" == "data_processing" ]; then
    python data_processing.py
else
    python logged_in_crawler.py
fi
