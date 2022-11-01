import csv
import gzip
import itertools
import json
import os
import time

from datetime import datetime, timedelta
from typing import List, Dict
from db.s3_conn import s3_conn
from utils import BaseService, stdout_log, slack_message_via_alertina
from config import DATE, DEFAULT_REQUIRED_CITIES


class DataProcessor(BaseService):
    def __init__(self, category: str):
        super().__init__()
        self.canton_codes = self._get_canton_codes()
        self.category = category
        self.previous_day_snapshot: Dict[str, dict] = self._get_previous_day_snapshot(DATE)
        self.previous_day_snapshot_ids: List[str] = [_id for _id in self.previous_day_snapshot]
        stdout_log.info(f"Previous day snapshot results -> len: {len(self.previous_day_snapshot_ids)}")

        self.scroll_results_from_today: List[dict] = self._get_deduplicated_scroll_results()
        self.scroll_results_from_today_ids: List[str] = [item["adId"] for item in self.scroll_results_from_today]
        stdout_log.info(f"Scroll results from today -> len: {len(self.scroll_results_from_today_ids)}")

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
            year, month, day = DATE.split('-')
            file_name: str = f"facebook-{self.category}-{city}-{year}-{month}-{day}.jsonl.gz"
            s3_conn.download_file(file_name, per_city=True)
            time.sleep(2)
            _input = gzip.GzipFile(file_name, "rb")
            for line in _input.readlines():
                item = json.loads(line)
                aggregated_scroll_results[item["adId"]] = item

            os.remove(file_name)
        return aggregated_scroll_results

    def _get_previous_day_snapshot(self, date) -> Dict[str, dict]:
        _date = datetime.strptime(date, '%Y-%m-%d') - timedelta(days=1)
        year, month, day = _date.strftime("%Y-%m-%d").split('-')
        file_name: str = f"{self.category}-snapshot-fb-{year}-{month}-{day}.jsonl.gz"
        s3_conn.download_file(file_name, 1)
        time.sleep(2)
        _input = gzip.GzipFile(file_name, "rb")
        previous_day_snapshot: Dict[str, dict] = {}
        for line in _input.readlines():
            record = json.loads(line)
            previous_day_snapshot[record["adId"]] = record
        stdout_log.info(f"Previous snapshot successfully collected.")

        return previous_day_snapshot

    def _get_deduplicated_scroll_results(self):
        """Func is doing a deduplication of the aggregated scroll results for all cities and loads it to the list.
        After deduplication non swiss records are removed."""

        aggregated_unique_scroll_results: Dict[str, dict] = self._aggregated_unique_scroll_results()
        stdout_log.info(f"Aggregated scroll results -> len: {len(aggregated_unique_scroll_results)}")

        unique_listings: List[dict] = list(aggregated_unique_scroll_results.values())
        stdout_log.info(f"Unique items of aggregated scroll results -> len: {len(unique_listings)}")

        if self.category == "vehicle":
            stdout_log.info("Excluding cars from vehicles.")
            car_items_from_today = self._read_file("snapshot-fb", "cars")
            cars_ids = [car["adId"] for car in car_items_from_today]

            unique_swiss_listings: List[dict] = [item for item in unique_listings if item.get("cantonCode")
                                                 in self.canton_codes and item.get("adId") not in cars_ids]
        else:
            unique_swiss_listings: List[dict] = [item for item in unique_listings if item.get("cantonCode")
                                                 in self.canton_codes]

        stdout_log.info(f"Unique SWISS items of aggregated scroll results -> len: {len(unique_swiss_listings)}")
        return unique_swiss_listings

    def listings_to_check(self):
        """Creates output file from listings which are in snapshot T-1 but not in scroll T0."""
        not_found_listings: List[dict] = [value for _id, value in self.previous_day_snapshot.items()
                                          if _id not in self.scroll_results_from_today_ids]
        file_name: str = f"{self.category}-listings-to-check-{DATE}.jsonl.gz"
        self._create_and_upload_file(file_name, not_found_listings)
        return not_found_listings

    def delta_listings(self):
        """Creates output file from listings which are in T0 scroll but not in T-1 snapshot (delta)."""
        delta_listings: List[dict] = [record for record in self.scroll_results_from_today
                                      if record["adId"] not in self.previous_day_snapshot_ids]
        file_name: str = f"{self.category}-delta-listings-{DATE}.jsonl.gz"
        self._create_and_upload_file(file_name, delta_listings)

    def overlap_listings(self):
        """Creates output file from listings which are bot in T-1 snapshot and T0 scroll."""
        overlap_listings: List[dict] = [record for _id, record in self.previous_day_snapshot.items()
                                        if _id in self.scroll_results_from_today_ids]
        file_name: str = f"{self.category}-overlap-listings-{DATE}.jsonl.gz"
        self._create_and_upload_file(file_name, overlap_listings)
        return overlap_listings

    def make_snapshot(self, delta_listings, checked_listings, overlap_listings):
        checked_listings = [self.previous_day_snapshot[item["adId"]] for item in checked_listings]
        snapshot_listings = list(itertools.chain.from_iterable([delta_listings, checked_listings, overlap_listings]))
        self._create_and_upload_file(f"{self.category}-snapshot-fb-{DATE}.jsonl.gz", snapshot_listings)

        # Send message to slack chanel via Alertina.
        slack_message_via_alertina(len(snapshot_listings), len(delta_listings), len(checked_listings),
                                   len(overlap_listings))
