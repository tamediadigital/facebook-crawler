import gzip
import json
import os
import time
import botocore


from datetime import datetime, timedelta
from logger import stdout_log
from s3_conn import s3_conn
from config import DATE

AGGREGATED_PREVIOUS_SEVEN_FILES: str = "aggregated_previous_seven_file.jsonl.gz"
YEAR, MONTH, DAY = DATE.split('-')


def delta():
    with gzip.open(AGGREGATED_PREVIOUS_SEVEN_FILES) as f:
        aggregated_previous_seven_files_listings: list = [json.loads(line) for line in f]

    stdout_log.info(f"Aggregated cities listings len: {len(aggregated_previous_seven_files_listings)}")

    previous_unique_ids: list = list(set([record["item_id"] for record in aggregated_previous_seven_files_listings]))
    stdout_log.info(f"Unique aggregated ids of listings for cities len: {len(previous_unique_ids)}")

    file_name: str = f"unique-facebook-aggregated-{YEAR}-{MONTH}-{DAY}.jsonl.gz"
    is_file_downloaded_from_s3: bool = True
    stdout_log.info(f"Downloading from S3: {file_name}")
    with gzip.open(f"unique-delta-facebook-aggregated-{YEAR}-{MONTH}-{DAY}.jsonl.gz", "wb") as writer:
        try:
            s3_conn.download_file(f'fb/year={YEAR}/month={MONTH}/day={DAY}/{file_name}', file_name)
            time.sleep(2)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                stdout_log.info(f"The object: {file_name} does not exist.")
            is_file_downloaded_from_s3 = False
        if is_file_downloaded_from_s3:
            _input = gzip.GzipFile(file_name, "rb")
            for line in _input.readlines():
                parsed_line = json.loads(line)
                if parsed_line["item_id"] not in previous_unique_ids:
                    writer.write(line)
            os.remove(file_name)
    writer.close()
    s3_conn.upload_file(f"unique-delta-facebook-aggregated-{YEAR}-{MONTH}-{DAY}.jsonl.gz", per_city=False)
    with gzip.open(f"unique-delta-facebook-aggregated-{YEAR}-{MONTH}-{DAY}.jsonl.gz") as f:
        delta_listings: list = [json.loads(line) for line in f]

    stdout_log.info(f"unique_delta_listings: {len(delta_listings)}")


def aggregate_previous_seven_files():
    curr_date_time_obj = datetime.strptime(DATE, '%Y-%m-%d')
    with gzip.open("aggregated_previous_seven_file.jsonl.gz", "wb") as writer:
        for i in range(1, 8):
            history_date_time_obj = curr_date_time_obj - timedelta(days=i)
            date_to_split = history_date_time_obj.strftime("%Y-%m-%d")
            YEAR, MONTH, DAY = date_to_split.split('-')
            file_name = f"unique-facebook-aggregated-{YEAR}-{MONTH}-{DAY}.jsonl.gz"
            stdout_log.info(f"Downloading from S3: {file_name}")
            is_file_downloaded_from_s3: bool = True
            try:
                s3_conn.download_file(f'fb/year={YEAR}/month={MONTH}/day={DAY}/{file_name}', file_name)
                time.sleep(2)
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == "404":
                    stdout_log.info(f"The object: {file_name} does not exist.")
                is_file_downloaded_from_s3 = False
            if is_file_downloaded_from_s3:
                _input = gzip.GzipFile(file_name, "rb")
                for line in _input.readlines():
                    writer.write(line)
                os.remove(file_name)
    writer.close()
    s3_conn.upload_file(AGGREGATED_PREVIOUS_SEVEN_FILES, per_city=False)


if __name__ == '__main__':
    aggregate_previous_seven_files()
    delta()
