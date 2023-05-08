import time
import random

from config import DATE
from typing import List
from parsers import Parser
from playwright.sync_api import sync_playwright
from utils import BaseService, Proxy, stdout_log, retry, LISTINGS


class DetailsCrawler(BaseService):

    def __init__(self, proxies: List[Proxy], parser: Parser, category: str):
        super().__init__()
        self.proxies = proxies
        self.parser = parser
        self.category = category
        self.items_to_paginate = self._read_file(LISTINGS.DELTA, category)
        self.paginated_items = []
        self.redis_key_for_urls_to_paginate = f"{category}-urls-to-paginate"
        self.redis_client.insert_into_redis([item for item in self.items_to_paginate],
                                            key=self.redis_key_for_urls_to_paginate)

    @retry(TimeoutError, stdout_log)
    def pagination_process(self):
        playwright = sync_playwright().start()
        i = 0
        executed_chunk_items = 0
        redis_items_to_paginate: list = self.redis_client.get_mappings(key=self.redis_key_for_urls_to_paginate)
        if redis_items_to_paginate:
            self.items_to_paginate = redis_items_to_paginate
        _items_to_paginate: list = self.items_to_paginate.copy()

        proxy_list_len = len(self.proxies) - 1
        proxy_switch = 0
        while True:
            chunk_from = self.listings_num_per_proxy * i + executed_chunk_items
            stdout_log.info(f"chunk_from: {chunk_from}")
            chunk_to = self.listings_num_per_proxy * (i + 1)
            stdout_log.info(f"chunk_to: {chunk_to}")
            stdout_log.info(f"proxy: {self.proxies[proxy_switch].server}")

            items_to_paginate: list = self.items_to_paginate[chunk_from:chunk_to]
            if not _items_to_paginate:
                break

            browser = playwright.firefox.launch(headless=True, proxy={
                "server": self.proxies[proxy_switch].server,
                "username": self.proxies[proxy_switch].username,
                "password": self.proxies[proxy_switch].password
                })
            i_context = browser.new_context()
            page = i_context.new_page()
            i += 1
            cookie_accepted = False
            error_happened = False
            for item in items_to_paginate:
                try:
                    url = item['url']
                    stdout_log.info(f"PAGE GO TO: {url}")
                    page.goto(url, wait_until="load", timeout=90000)
                    time.sleep(random.choice(self.page_timeout_paginating_pool))
                    if not cookie_accepted and "next" not in page.url:
                        # Cookies step.
                        page.click("span:text('Decline optional cookies')")
                        time.sleep(2)
                        stdout_log.info("Cookies step completed.")
                        cookie_accepted = True

                    # Not alive listing url example: "https://www.facebook.com/?next=%2Fmarketplace%2F"
                    # Available listing but bad proxy url example:
                    # "https://www.facebook.com/login/?next=https%3A%2F%2Fwww.facebook.com%2Fmarketplace%2Fitem%2F542404617581262"
                    # With this condition we only paginate available listings
                    page_url = page.url
                    if "login" not in page_url and "next" not in page_url:
                        stdout_log.info("Collecting listing details.")
                        parsed_item = self.parser.parse_item(page.content(), item, self.category)
                        if parsed_item:
                            self.paginated_items.append(parsed_item)
                except Exception as e:
                    stdout_log.error(f"Error occurs! {e}")
                    page.close()
                    browser.close()
                    i -= 1
                    error_happened = True
                    break

                executed_chunk_items += 1
                stdout_log.info(f"Executed chunk items {executed_chunk_items}")
                _items_to_paginate.remove(item)
                self.redis_client.insert_into_redis(_items_to_paginate, key=self.redis_key_for_urls_to_paginate)

            executed_chunk_items = 0 if not error_happened else executed_chunk_items
            stdout_log.info(f"Executed chunk items {executed_chunk_items}")
            page.close()
            browser.close()

            # Call rotate proxy.
            self.proxies[proxy_switch].rotate_proxy_call()
            if proxy_switch == proxy_list_len:
                proxy_switch = 0
            else:
                proxy_switch += 1

        file_name: str = f"{self.category}-{LISTINGS.PAGINATED_DELTA}-{DATE}.jsonl.gz"
        self._create_and_upload_file(file_name, self.paginated_items)
        stdout_log.info("Process: items_pagination_process finished.")
        time.sleep(2)
        playwright.stop()
        return self.paginated_items
