import gzip
import json
import time


from playwright.sync_api import sync_playwright
from crawlers.automotive_crawlers.base_automotive_crawler import BaseCarsCrawler
from utils.logger import stdout_log
from parsers.automotive_parsers import parse_car
from parsers.base_parsers import is_see_more
from utils.proxy import Proxy
from utils.retry_handler import retry
from config import DATE


class DeltaCarsCrawler(BaseCarsCrawler):
    _FILE_NAME_PREFIX = "delta-listings"

    def __init__(self, proxy: Proxy):
        super().__init__(proxy)
        self.items_to_paginate = self._items_to_paginate(self._FILE_NAME_PREFIX)
        self.paginated_items = []
        self.redis_client.insert_into_redis([item for item in self.items_to_paginate], key="car-urls-to-paginate")

    def _items_to_paginate(self, file_name_prefix: str) -> list:
        y, m, d = DATE.split('-')
        file_to_download = f"{file_name_prefix}-{y}-{m}-{d}.jsonl.gz"
        self.s3_conn.download_file(file_to_download)
        time.sleep(3)
        _input = gzip.GzipFile(file_to_download, "rb")
        return [json.loads(line) for line in _input.readlines()]

    @retry(TimeoutError, stdout_log)
    def get_details_for_delta_cars_process(self):
        playwright = sync_playwright().start()
        i = 0
        executed_chunk_items = 0
        redis_items_to_paginate: list = self.redis_client.get_mappings(key="car-urls-to-paginate")
        if redis_items_to_paginate:
            self.items_to_paginate = redis_items_to_paginate
        _items_to_paginate: list = self.items_to_paginate.copy()

        while True:
            chunk_from = self.listings_num_per_proxy * i + executed_chunk_items
            stdout_log.info(f"chunk_from: {chunk_from}")
            chunk_to = self.listings_num_per_proxy * (i + 1)
            stdout_log.info(f"chunk_to: {chunk_to}")

            items_to_paginate: list = self.items_to_paginate[chunk_from:chunk_to]
            if not _items_to_paginate:
                break

            browser = playwright.firefox.launch(headless=True, proxy={
                "server": self.proxy.server,
                "username": self.proxy.username,
                "password": self.proxy.password
                })
            i_context = browser.new_context()

            i += 1
            cookie_accepted = False
            error_happened = False
            for item in items_to_paginate:
                page = i_context.new_page()
                try:
                    url = item['url']
                    stdout_log.info(f"PAGE GO TO: {url}")
                    page.goto(url, wait_until="load", timeout=90000)
                    time.sleep(5)
                    if not cookie_accepted and "next" not in page.url:
                        # Allow essential cookies step.
                        page.click("span:text('Only allow essential cookies')")
                        time.sleep(2)
                        stdout_log.info("Essential cookies step completed.")
                        cookie_accepted = True

                    # Not alive listing url example: "https://www.facebook.com/?next=%2Fmarketplace%2F"
                    # Available listing but bad proxy url example:
                    # "https://www.facebook.com/login/?next=https%3A%2F%2Fwww.facebook.com%2Fmarketplace%2Fitem%2F542404617581262"
                    page_url = page.url
                    if "login" not in page_url and "next" not in page_url:
                        stdout_log.info("Available listing.")
                        if is_see_more(page.content()):
                            page.click('span:text("See More") >> nth=1')
                            time.sleep(0.5)
                            parsed_item = parse_car(page.content(), item, see_more=True)
                            if parsed_item:
                                self.paginated_items.append(parsed_item)
                        else:
                            parsed_item = parse_car(page.content(), item)
                            if parsed_item:
                                self.paginated_items.append(parsed_item)
                    elif "login" in page_url and "next" in page_url:
                        stdout_log.error(f"Proxy dead on url: {page.url}")
                        page.close()
                        browser.close()
                        i -= 1
                        error_happened = True
                        break
                except Exception as e:
                    stdout_log.error(f"Error occurs! {e}")
                    page.close()
                    browser.close()
                    i -= 1
                    error_happened = True
                    break
                page.close()
                executed_chunk_items += 1
                stdout_log.info(f"Executed chunk items {executed_chunk_items}")
                _items_to_paginate.remove(item)
                self.redis_client.insert_into_redis(_items_to_paginate, key="car-urls-to-paginate")

            executed_chunk_items = 0 if not error_happened else executed_chunk_items
            stdout_log.info(f"Executed chunk items {executed_chunk_items}")
            browser.close()

            # Call rotate proxy.
            self.proxy.rotate_proxy_call()

        file_name: str = f"facebook-delta-paginated-{DATE}.jsonl.gz"
        self._create_and_upload_file(file_name, self.paginated_items)
        stdout_log.info("Get details for delta cars process finished.")
        time.sleep(2)
        playwright.stop()
        return self.paginated_items
