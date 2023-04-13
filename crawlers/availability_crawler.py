import time
import random

from typing import List
from datetime import datetime
from playwright.sync_api import sync_playwright
from config import DATE, PROXIES_BANNED_THRESHOLD
from utils import Proxy, BaseService, stdout_log, retry, LISTINGS, regex_search_between, \
    slack_alert_when_proxy_is_blocked


class AvailabilityCrawler(BaseService):
    def __init__(self, proxies: List[Proxy], category: str):
        super().__init__()
        self.proxies = proxies
        self.proxies_banned_threshold = {p.server: 0 for p in proxies}
        self.proxies_banned_slack_alert = {p.server: False for p in proxies}

        self.category = category
        self.items_to_check = self._read_file(LISTINGS.TO_CHECK, category)
        self.available_items = []
        self.redis_key_for_urls_to_check = f"{category}-urls-to-check"
        self.redis_client.insert_into_redis([item for item in self.items_to_check], key=self.redis_key_for_urls_to_check)

    @staticmethod
    def _is_sold(page_content: str):
        _title: str = regex_search_between(page_content, '"marketplace_listing_title":"', '","condition"') or \
                     regex_search_between(page_content, '"marketplace_listing_title":"', '","inventory_count"') or \
                     regex_search_between(page_content, '"marketplace_listing_title":"', '","is_pending"') or \
                     regex_search_between(page_content, '"marketplace_listing_title":"', '","is_live"') or \
                     regex_search_between(page_content, '"meta":{"title":"', ' - Cars & Trucks') or \
                     regex_search_between(page_content, '"meta":{"title":"', ' - Miscellaneous') or \
                     regex_search_between(page_content, '"meta":{"title":"', ' - Property Rentals') or \
                     regex_search_between(page_content, '"meta":{"title":"', ' - Property For Sale')

        title = _title if _title else ""
        if "Sold" in title:
            stdout_log.info("Listing is Sold!")
            return True
        return False

    @retry(TimeoutError, stdout_log)
    def availability_check_process(self):
        playwright = sync_playwright().start()
        i = 0
        executed_chunk_items = 0
        redis_items_to_check: list = self.redis_client.get_mappings(key=self.redis_key_for_urls_to_check)
        if redis_items_to_check:
            self.items_to_check = redis_items_to_check
        _items_to_check: list = self.items_to_check.copy()

        proxy_list_len = len(self.proxies) - 1
        proxy_switch = 0
        while True:
            chunk_from = self.listings_num_per_proxy * i + executed_chunk_items
            stdout_log.info(f"chunk_from: {chunk_from}")
            chunk_to = self.listings_num_per_proxy * (i + 1)
            stdout_log.info(f"chunk_to: {chunk_to}")
            stdout_log.info(f"proxy: {self.proxies[proxy_switch].server}")

            items_to_check: list = self.items_to_check[chunk_from:chunk_to]
            if not _items_to_check:
                break

            proxy_server = self.proxies[proxy_switch].server
            browser = playwright.firefox.launch(headless=True, proxy={
                "server": proxy_server,
                "username": self.proxies[proxy_switch].username,
                "password": self.proxies[proxy_switch].password
                })
            i_context = browser.new_context()

            i += 1
            cookie_accepted = False
            error_happened = False
            for item in items_to_check:
                page = i_context.new_page()
                url = item['url']
                if self.proxies_banned_threshold[proxy_server] < PROXIES_BANNED_THRESHOLD:
                    try:
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
                        number_of_log_in_screens_in_row = self.proxies_banned_threshold[proxy_server]
                        if "login" not in page_url and "next" not in page_url:
                            stdout_log.info("Available listing.")
                            # Here we are checking if listing contains mark "Sold" in title if contains we are excluding it.
                            if not self._is_sold(page.content()):
                                item['last_check'] = str(datetime.now())
                                self.available_items.append(item)
                            if number_of_log_in_screens_in_row:
                                self.proxies_banned_threshold[proxy_server] = 0
                        elif "login" in page_url and "next" in page_url:
                            stdout_log.info(f"Proxy {proxy_server} probably blocked!")
                            self.proxies_banned_threshold[proxy_server] = number_of_log_in_screens_in_row + 1

                    except Exception as e:
                        stdout_log.error(f"Error occurs! {e}")
                        page.close()
                        browser.close()
                        i -= 1
                        error_happened = True
                        break
                else:
                    if not self.proxies_banned_slack_alert[proxy_server]:
                        slack_alert_when_proxy_is_blocked(proxy_server)
                        self.proxies_banned_slack_alert[proxy_server] = True

                    stdout_log.error(f"Proxy {proxy_server} blocked! Keep listing: {url}")
                    item['last_check'] = str(datetime.now())
                    self.available_items.append(item)

                page.close()
                executed_chunk_items += 1
                stdout_log.info(f"Executed chunk items {executed_chunk_items}")
                _items_to_check.remove(item)
                self.redis_client.insert_into_redis(_items_to_check, key=self.redis_key_for_urls_to_check)

            executed_chunk_items = 0 if not error_happened else executed_chunk_items
            stdout_log.info(f"Executed chunk items {executed_chunk_items}")
            browser.close()

            # Call rotate proxy.
            self.proxies[proxy_switch].rotate_proxy_call()
            if proxy_switch == proxy_list_len:
                proxy_switch = 0
            else:
                proxy_switch += 1

        file_name: str = f"{self.category}-{LISTINGS.AVAILABLE}-{DATE}.jsonl.gz"
        self._create_and_upload_file(file_name, self.available_items)
        stdout_log.info(f"{self.category} availability check process finished.")
        time.sleep(2)
        playwright.stop()
        return self.available_items
