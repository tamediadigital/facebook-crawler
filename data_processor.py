import csv
import gzip
import itertools
import json
import os
import time

from typing import List, Dict
from crawlers.base_crawler import BaseCrawler
from db.s3_conn import s3_conn
from utils.logger import stdout_log
from config import DATE, DEFAULT_REQUIRED_CITIES


class DataProcessor(BaseCrawler):
    def __init__(self):
        super().__init__()
        self.canton_codes = self._get_canton_codes()

        self.previous_day_snapshot: Dict[str, dict] = self._get_previous_day_snapshot(DATE)
        self.previous_day_snapshot_ids: List[str] = [_id for _id in self.previous_day_snapshot]
        stdout_log.info(f"Previous day snapshot results -> len: {len(self.previous_day_snapshot_ids)}")

        self.scroll_results_from_today: List[dict] = self._get_deduplicated_scroll_results()
        self.scroll_results_from_today_ids: List[str] = [item["ad_id"] for item in self.scroll_results_from_today]
        stdout_log.info(f"Scroll results from today -> len: {len(self.scroll_results_from_today_ids)}")

    @staticmethod
    def _get_canton_codes() -> List[str]:
        """Func gets the canton codes from csv file and loads it to the list."""
        file = open('new_codes.csv', encoding='UTF8')
        csvreader = csv.DictReader(file)
        return [row['cantonCode'] for row in csvreader]

    @staticmethod
    def _aggregated_unique_scroll_results() -> Dict[str, dict]:
        """Func downloads scroll results for all cities and aggregates and deduplicate it and loads it to the list.
        After aggregation files are deleted."""

        aggregated_scroll_results: Dict = {}
        for city in DEFAULT_REQUIRED_CITIES:
            year, month, day = DATE.split('-')
            file_name: str = f"facebook-{city}-{year}-{month}-{day}.jsonl.gz"
            s3_conn.download_file(file_name, per_city=True)
            time.sleep(2)
            _input = gzip.GzipFile(file_name, "rb")
            for line in _input.readlines():
                item = json.loads(line)
                aggregated_scroll_results[item["ad_id"]] = item

            os.remove(file_name)
        return aggregated_scroll_results

    def _get_deduplicated_scroll_results(self):
        """Func is doing a deduplication of the aggregated scroll results for all cities and loads it to the list.
        After deduplication non swiss records are removed."""

        aggregated_unique_scroll_results: Dict[str, dict] = self._aggregated_unique_scroll_results()
        stdout_log.info(f"Aggregated scroll results -> len: {len(aggregated_unique_scroll_results)}")

        unique_listings: List[dict] = list(aggregated_unique_scroll_results.values())
        stdout_log.info(f"Unique items of aggregated scroll results -> len: {len(unique_listings)}")
        unique_swiss_listings: List[dict] = [item for item in unique_listings if item.get("canton_code")
                                             in self.canton_codes]
        stdout_log.info(f"Unique SWISS items of aggregated scroll results -> len: {len(unique_swiss_listings)}")
        return unique_swiss_listings

    def listings_to_check(self):
        """Creates output file from listings which are in snapshot T-1 but not in scroll T0."""
        not_found_listings: List[dict] = [value for _id, value in self.previous_day_snapshot.items()
                                          if _id not in self.scroll_results_from_today_ids]
        file_name: str = f"listings-to-check-{DATE}.jsonl.gz"
        self._create_and_upload_file(file_name, not_found_listings)

    def delta_listings(self):
        """Creates output file from listings which are in T0 scroll but not in T-1 snapshot (delta)."""
        delta_listings: List[dict] = [record for record in self.scroll_results_from_today
                                      if record["ad_id"] not in self.previous_day_snapshot_ids]
        file_name: str = f"delta-listings-{DATE}.jsonl.gz"
        self._create_and_upload_file(file_name, delta_listings)

    def overlap_listings(self):
        """Creates output file from listings which are bot in T-1 snapshot and T0 scroll."""
        overlap_listings: List[dict] = [record for _id, record in self.previous_day_snapshot.items()
                                        if _id in self.scroll_results_from_today_ids]
        file_name: str = f"overlap-listings-{DATE}.jsonl.gz"
        self._create_and_upload_file(file_name, overlap_listings)
        return overlap_listings

    def make_snapshot(self, delta_listings, checked_listings, overlap_listings):
        checked_listings = [self.previous_day_snapshot[item["ad_id"]] for item in checked_listings]
        snapshot_listings = list(itertools.chain.from_iterable([delta_listings, checked_listings, overlap_listings]))
        self._create_and_upload_file(f"snapshot-fb-{DATE}.jsonl.gz", snapshot_listings)
