import gzip
import json
import time

from playwright.sync_api import sync_playwright
from logger import stdout_log
from s3_conn import s3_conn
from config_for_testing import DATE, PROXYEMPIRE_SERVER, PROXYEMPIRE_MOBILE_USERNAME, PROXYEMPIRE_MOBILE_PASS
from datetime import timedelta, datetime


class BasePagination:
    def __init__(self, proxy_server: str, proxy_username: str, proxy_password: str, file_to_download: str):
        self.proxy_server = proxy_server
        self.proxy_username = proxy_username
        self.proxy_password = proxy_password
        self.file_to_download = file_to_download
        self.items_to_paginate = self._items_to_paginate()

    def _items_to_paginate(self) -> list:
        curr_date_time_obj = datetime.strptime(DATE, '%Y-%m-%d')
        _date = curr_date_time_obj - timedelta(days=1)
        date = _date.strftime("%Y-%m-%d")
        YEAR, MONTH, DAY = date.split('-')
        s3_conn.download_file(f'fb/year={YEAR}/month={MONTH}/day={DAY}/{self.file_to_download}',
                              self.file_to_download)
        time.sleep(3)
        _input = gzip.GzipFile(self.file_to_download, "rb")
        return [json.loads(line) for line in _input.readlines()]

    def pagination(self):
        playwright = sync_playwright().start()
        i = 0
        paginated_items: list = []
        executed_chunk_items = 0
        while True:
            chunk_len = 5

            chunk_from = chunk_len * i + executed_chunk_items
            stdout_log.info(f"chunk_from: {chunk_from}")
            chunk_to = chunk_len * (i + 1)
            stdout_log.info(f"chunk_to: {chunk_to}")
            items_to_paginate: list = self.items_to_paginate[chunk_from:chunk_to]  # mutable obj issue???
            if not items_to_paginate:
                break

            # without proxy server
            # browser = playwright.firefox.launch(headless=True, timeout=60000)

            # with proxy-empire mobile proxy server
            browser = playwright.firefox.launch(headless=True, proxy={
                "server": self.proxy_server,
                "username": self.proxy_username,
                "password": self.proxy_password
                })

            i_context = browser.new_context()

            i += 1
            cookie_accepted = False
            error_happened = False
            for item in items_to_paginate:
                page = i_context.new_page()
                try:
                    url = f"https://www.facebook.com{item['item_url']}"
                    stdout_log.info(f"PAGE GO TO: {url}")
                    page.goto(url)
                    time.sleep(5)
                    if not cookie_accepted:
                        # Allow essential cookies step
                        page.click("span:text('Only allow essential cookies')")
                        time.sleep(2)
                        stdout_log.info("Essential cookies step completed.")
                        cookie_accepted = True
                    # check if the listing is alive or not
                    # ...

                    # collect the data
                    # ...
                except Exception as e:
                    stdout_log.error("Error occurs!")
                    page.close()
                    browser.close()
                    i -= 1
                    error_happened = True
                    break
                page.close()
                executed_chunk_items += 1
                stdout_log.info(f"Executed chunk items {executed_chunk_items}")

            executed_chunk_items = 0 if not error_happened else executed_chunk_items
            stdout_log.info(f"Executed chunk items {executed_chunk_items}")
            browser.close()

            # call rotate proxy
            # ....

            # Break after first 5 to test bandwidth usage.
            stdout_log.info("Break after first 5 to test bandwidth usage.")
            break

        stdout_log.info("pagination_processor.pagination() finished.")


if __name__ == '__main__':
    pagination_processor: BasePagination = BasePagination(PROXYEMPIRE_SERVER,
                                                          PROXYEMPIRE_MOBILE_USERNAME,
                                                          PROXYEMPIRE_MOBILE_PASS,
                                                          "unique-delta-facebook-aggregated-2022-09-06.jsonl.gz")
    stdout_log.info("BasePagination init.")
    pagination_processor.pagination()
    stdout_log.info("pagination_processor.pagination() started.")
