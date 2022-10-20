import gzip
import json
import time

from typing import List
from utils.logger import stdout_log
from db import s3_conn, redis_client
from config import PAGE_HEIGHT_SCROLL_POOL, PAGE_TIMEOUT_SCROLL_POOL, DATE, LISTINGS_NUM_PER_PROXY


class BaseService:
    def __init__(self):
        self.s3_conn = s3_conn
        self.redis_client = redis_client
        self.page_height_scroll_pool = PAGE_HEIGHT_SCROLL_POOL
        self.page_timeout_scroll_pool = PAGE_TIMEOUT_SCROLL_POOL
        self.listings_num_per_proxy = LISTINGS_NUM_PER_PROXY

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

    def _create_and_upload_file(self, file_name: str, listings: List[dict], per_city=False):
        self._create_file(file_name, listings)
        time.sleep(1)
        self._upload_file(file_name, per_city)
        time.sleep(1)

    def _read_file(self, file_prefix, category) -> list:
        y, m, d = DATE.split('-')
        file_to_download = f"{category}-{file_prefix}-{y}-{m}-{d}.jsonl.gz"
        self.s3_conn.download_file(file_to_download)
        time.sleep(3)
        _input = gzip.GzipFile(file_to_download, "rb")
        return [json.loads(line) for line in _input.readlines()]
