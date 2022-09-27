import csv
import gzip
import json
import os
import time

from typing import List, Dict
from s3_conn import s3_conn
from logger import stdout_log
from config import DATE, DEFAULT_REQUIRED_CITIES
from datetime import datetime, timedelta


class ScrollDataProcessor:
    def __init__(self, date: str):
        self.date: str = date
        self.canton_codes: List[str] = self._get_canton_codes()

    @staticmethod
    def _get_canton_codes() -> List[str]:
        """Func gets the canton codes from csv file and loads it to the list."""
        file = open('new_codes.csv', encoding='UTF8')
        csvreader = csv.DictReader(file)
        return [row['cantonCode'] for row in csvreader]

    def _aggregated_unique_scroll_results(self) -> Dict[str, dict]:
        """Func downloads scroll results for all cities and aggregates and deduplicate it and loads it to the list.
        After aggregation files are deleted."""

        aggregated_scroll_results: Dict = {}
        for city in DEFAULT_REQUIRED_CITIES:
            year, month, day = self.date.split('-')
            file_name: str = f"facebook-{city}-{year}-{month}-{day}.jsonl.gz"
            s3_conn.download_file(file_name, per_city=True)
            time.sleep(2)
            _input = gzip.GzipFile(file_name, "rb")
            for line in _input.readlines():
                item = json.loads(line)
                aggregated_scroll_results[item["ad_id"]] = item

            os.remove(file_name)
        return aggregated_scroll_results

    def get_deduplicated_scroll_results(self):
        """Func is doing a deduplication of the aggregated scroll results for all cities and loads it to the list.
        After deduplication non swiss records are removed."""

        aggregated_unique_scroll_results: Dict[str, dict] = self._aggregated_unique_scroll_results()
        stdout_log.info(f"Aggregated scroll results -> len: {len(aggregated_unique_scroll_results)}")

        unique_listings: List[dict] = list(aggregated_unique_scroll_results.values())
        stdout_log.info(f"Unique items of aggregated scroll results -> len: {len(unique_listings)}")
        unique_swiss_listings: List[dict] = [item for item in unique_listings if item.get("canton_code")
                                             in self.canton_codes]
        stdout_log.info(f"Unique SWISS items of aggregated scroll results -> len: {len(unique_swiss_listings)}")

        # TODO: Remove snapshot creation from here.
        year, month, day = self.date.split('-')
        unique_aggregated_file: str = f"snapshot-fb-{year}-{month}-{day}.jsonl.gz"
        with gzip.open(unique_aggregated_file, "wb") as writer:
            for line in unique_swiss_listings:
                json_str = json.dumps(line) + "\n"
                json_bytes = json_str.encode('utf-8')
                writer.write(json_bytes)
        writer.close()
        s3_conn.upload_file(unique_aggregated_file, per_city=False)

        return unique_swiss_listings


class DataProcessor:
    def __init__(self, date, scroll_results_from_today):
        self.date: str = date
        self.previous_day_snapshot: List[dict] = self._get_previous_day_snapshot()
        self.previous_day_snapshot_ids: List[str] = [item["ad_id"] for item in self.previous_day_snapshot]
        stdout_log.info(f"Previous day snapshot results -> len: {len(self.previous_day_snapshot_ids)}")
        self.scroll_results_from_today: List[dict] = scroll_results_from_today
        self.scroll_results_from_today_ids: List[str] = [item["ad_id"] for item in self.scroll_results_from_today]
        stdout_log.info(f"Scroll results from today -> len: {len(self.scroll_results_from_today_ids)}")

    @staticmethod
    def _create_and_upload_file(file_name: str, listings: List[dict]):
        with gzip.open(file_name, "wb") as writer:
            for line in listings:
                json_str = json.dumps(line) + "\n"
                json_bytes = json_str.encode('utf-8')
                writer.write(json_bytes)
        writer.close()
        s3_conn.upload_file(file_name, per_city=False)
        stdout_log.info(f"File -> {file_name} successfully uploaded on S3.")
        stdout_log.info(f"File len -> {len(listings)}.")

    def _get_previous_day_snapshot(self) -> List[dict]:
        _date = datetime.strptime(self.date, '%Y-%m-%d') - timedelta(days=1)
        year, month, day = _date.strftime("%Y-%m-%d").split('-')
        file_name: str = f"snapshot-fb-{year}-{month}-{day}.jsonl.gz"
        s3_conn.download_file(file_name, 1)
        time.sleep(2)
        _input = gzip.GzipFile(file_name, "rb")
        previous_day_snapshot: List[dict] = [json.loads(line) for line in _input.readlines()]
        stdout_log.info(f"Previous snapshot successfully collected.")
        return previous_day_snapshot

    def not_found_listings(self):
        """Creates output file from listings which are in snapshot T-1 but not in scroll T0."""
        not_found_listings: List[dict] = [record for record in self.previous_day_snapshot
                                          if record["ad_id"] not in self.scroll_results_from_today_ids]
        file_name: str = f"not-found-listings-in-scroll-{self.date}.jsonl.gz"
        self._create_and_upload_file(file_name, not_found_listings)

    def delta_listings(self):
        """Creates output file from listings which are in T0 scroll but not in T-1 snapshot (delta)."""
        delta_listings: List[dict] = [record for record in self.scroll_results_from_today
                                      if record["ad_id"] not in self.previous_day_snapshot_ids]
        file_name: str = f"delta-listings-{self.date}.jsonl.gz"
        self._create_and_upload_file(file_name, delta_listings)

    def overlap_listings(self):
        """Creates output file from listings which are bot in T-1 snapshot and T0 scroll."""
        overlap_listings: List[dict] = [record for record in self.scroll_results_from_today
                                        if record["ad_id"] in self.previous_day_snapshot_ids]
        file_name: str = f"overlap-listings-{self.date}.jsonl.gz"
        self._create_and_upload_file(file_name, overlap_listings)


if __name__ == '__main__':
    scroll_data_processor: ScrollDataProcessor = ScrollDataProcessor(DATE)
    deduplicated_scroll_results: List[dict] = scroll_data_processor.get_deduplicated_scroll_results()
    data_processor: DataProcessor = DataProcessor(DATE, deduplicated_scroll_results)
    data_processor.not_found_listings()
    data_processor.delta_listings()
    data_processor.overlap_listings()
