import random
import time

from playwright.sync_api import sync_playwright
from utils import Proxy, BaseService, stdout_log, retry, LISTINGS
from config import DATE


class AvailabilityCrawler(BaseService):
    def __init__(self, proxy: Proxy, category: str):
        super().__init__()
        self.proxy = proxy
        self.category = category
        self.items_to_check = self._read_file(LISTINGS.TO_CHECK, category)
        self.available_items = []
        self.redis_key_for_urls_to_check = f"{category}-urls-to-check"
        self.redis_client.insert_into_redis([item for item in self.items_to_check], key=self.redis_key_for_urls_to_check)

    @retry(TimeoutError, stdout_log)
    def availability_check_process(self):
        playwright = sync_playwright().start()
        i = 0
        executed_chunk_items = 0
        redis_items_to_check: list = self.redis_client.get_mappings(key=self.redis_key_for_urls_to_check)
        if redis_items_to_check:
            self.items_to_check = redis_items_to_check
        _items_to_check: list = self.items_to_check.copy()

        while True:
            chunk_from = self.listings_num_per_proxy * i + executed_chunk_items
            stdout_log.info(f"chunk_from: {chunk_from}")
            chunk_to = self.listings_num_per_proxy * (i + 1)
            stdout_log.info(f"chunk_to: {chunk_to}")

            items_to_check: list = self.items_to_check[chunk_from:chunk_to]
            if not _items_to_check:
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
            for item in items_to_check:
                page = i_context.new_page()
                try:
                    url = item['url']
                    stdout_log.info(f"PAGE GO TO: {url}")
                    page.set_default_timeout(90000)
                    page.goto(url, wait_until="load")
                    time.sleep(random.choice(self.page_timeout_paginating_pool))
                    if not cookie_accepted and "next" not in page.url:
                        # Allow essential cookies step.
                        page.click("span:text('Only allow essential cookies')")
                        time.sleep(2)
                        stdout_log.info("Essential cookies step completed.")
                        cookie_accepted = True

                    # Not alive listing url example: "https://www.facebook.com/?next=%2Fmarketplace%2F"
                    # Available listing but bad proxy url example:
                    # "https://www.facebook.com/login/?next=https%3A%2F%2Fwww.facebook.com%2Fmarketplace%2Fitem%2F542404617581262"
                    # With this condition we only paginate available listings
                    page_url = page.url
                    if "login" not in page_url and "next" not in page_url:
                        stdout_log.info("Available listing.")
                        self.available_items.append(item)
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
                _items_to_check.remove(item)
                self.redis_client.insert_into_redis(_items_to_check, key=self.redis_key_for_urls_to_check)

            executed_chunk_items = 0 if not error_happened else executed_chunk_items
            stdout_log.info(f"Executed chunk items {executed_chunk_items}")
            browser.close()

            # Call rotate proxy.
            self.proxy.rotate_proxy_call()

        file_name: str = f"{self.category}-{LISTINGS.AVAILABLE}-{DATE}.jsonl.gz"
        self._create_and_upload_file(file_name, self.available_items)
        stdout_log.info(f"{self.category} availability check process finished.")
        time.sleep(2)
        playwright.stop()
        return self.available_items
