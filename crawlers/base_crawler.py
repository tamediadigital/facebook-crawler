import gzip
import json
import time
from datetime import datetime, timedelta

from typing import List, Dict
from utils.logger import stdout_log
from db.s3_conn import s3_conn


class BaseCrawler:
    def __init__(self):
        self.s3_conn = s3_conn

    @staticmethod
    def _create_file(file_name: str, listings: List[dict]):
        with gzip.open(file_name, "wb") as writer:
            for line in listings:
                json_str = json.dumps(line) + "\n"
                json_bytes = json_str.encode('utf-8')
                writer.write(json_bytes)
        writer.close()
        stdout_log.info(f"File -> {file_name} successfully created.")
        stdout_log.info(f"File len -> {len(listings)}.")

    @staticmethod
    def _upload_file(file_name: str, per_city: bool):
        s3_conn.upload_file(file_name, per_city)
        stdout_log.info(f"File -> {file_name} successfully uploaded on S3.")

    @staticmethod
    def _get_previous_day_snapshot(date) -> Dict[str, dict]:
        _date = datetime.strptime(date, '%Y-%m-%d') - timedelta(days=1)
        year, month, day = _date.strftime("%Y-%m-%d").split('-')
        file_name: str = f"snapshot-fb-{year}-{month}-{day}.jsonl.gz"
        s3_conn.download_file(file_name, 1)
        time.sleep(2)
        _input = gzip.GzipFile(file_name, "rb")
        previous_day_snapshot: Dict[str, dict] = {}
        for line in _input.readlines():
            record = json.loads(line)
            previous_day_snapshot[record["ad_id"]] = record
        stdout_log.info(f"Previous snapshot successfully collected.")
        return previous_day_snapshot

    def _create_and_upload_file(self, file_name: str, listings: List[dict], per_city=False):
        self._create_file(file_name, listings)
        time.sleep(1)
        self._upload_file(file_name, per_city)
        time.sleep(1)


