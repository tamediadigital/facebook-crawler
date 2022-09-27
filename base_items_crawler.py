import gzip
import itertools
import json
import time
import random
import requests

from typing import List
from playwright.sync_api import sync_playwright
from config import CITIES_CITIES_CODE_MAP, DATE, SOCIAL_PROXY_SERVER, SOCIAL_PROXY_USERNAME, REQUIRED_CITIES, \
    SOCIAL_PROXY_PASS, SOCIAL_PROXY_B64_STR, SOCIAL_PROXY_KEY, SOCIAL_PROXY_SECRET, PRICE_COMBINATIONS
from logger import stdout_log
from redis_db import redis_client
from retry_handler import retry
from s3_conn import s3_conn
from parsers import parse_base_item


class FacebookBaseItemsCrawler:
    def __init__(self):
        self.s3_conn = s3_conn
        self.redis_client = redis_client
        self.required_cities = REQUIRED_CITIES
        self.price_combinations = PRICE_COMBINATIONS

    @staticmethod
    def _make_file_obj(parsed_items_for_city: List[list], file: str):
        chained_list_of_items: list = list(itertools.chain.from_iterable(parsed_items_for_city))
        with gzip.open(file, "wb") as writer:
            for item in chained_list_of_items:
                json_str = json.dumps(item) + "\n"
                json_bytes = json_str.encode('utf-8')
                writer.write(json_bytes)

        writer.close()
        stdout_log.info(f"File object been made: {file}")
        return file

    @staticmethod
    def _rotate_proxy_call():
        stdout_log.info(f"Rotate proxy call triggered.")
        url: str = f"https://thesocialproxy.com/wp-json/lmfwc/v2/licenses/rotate-proxy/{SOCIAL_PROXY_B64_STR}" \
                   f"/?consumer_key={SOCIAL_PROXY_KEY}&consumer_secret={SOCIAL_PROXY_SECRET}"

        payload = {}
        headers = {
            'Content-Type': 'application/json'
            }

        proxy_list: list = json.loads(requests.request("GET", url, headers=headers, data=payload).text)
        stdout_log.info(proxy_list)

    @retry(TimeoutError, stdout_log)
    def crawling_process(self):
        redis_required_cities: list = self.redis_client.get_mappings(key="base-items-crawler-cities")
        if redis_required_cities:
            self.required_cities = redis_required_cities

        # Init browser, page with proxy
        stdout_log.info("Init step started.")
        playwright = sync_playwright().start()

        un_crawled_cities: list = self.required_cities.copy()
        for city in self.required_cities:
            redis_required_prices: list = self.redis_client.get_mappings(key="base-items-crawler-prices")
            if redis_required_prices:
                self.price_combinations = redis_required_prices

            redis_parsed_items_for_city: list = self.redis_client.get_mappings(key="parsed-items-for-city")
            parsed_items_for_city: list = redis_parsed_items_for_city if redis_parsed_items_for_city else []

            city_code: str = CITIES_CITIES_CODE_MAP[city]
            un_crawled_prices: list = self.price_combinations.copy()
            for p_comb in self.price_combinations:
                browser = playwright.firefox.launch(headless=True, proxy={
                    "server": SOCIAL_PROXY_SERVER,
                    "username": SOCIAL_PROXY_USERNAME,
                    "password": SOCIAL_PROXY_PASS
                    })
                i_context = browser.new_context()
                page = i_context.new_page()
                try:
                    start_url: str = f"https://www.facebook.com/marketplace/{city_code}/cars/{p_comb}"
                    stdout_log.info(f"City: {city}")
                    stdout_log.info(f"PAGE GOING TO: {start_url}")
                    page.goto(start_url)
                    time.sleep(5)

                    # Allow essential cookies step
                    page.click("span:text('Only allow essential cookies')")
                    time.sleep(2)
                    stdout_log.info("Essential cookies step completed.")
                    stdout_log.info(f"PAGE ON URL: {page.url}")

                    # Scroll step.
                    page_height_after_scroll: int = 0
                    page_height: int = 1
                    while True:
                        stdout_log.info(f"Page height {page_height}")
                        if page_height == page_height_after_scroll:
                            stdout_log.info("Same page height before and after scroll stopped scrolling!")
                            if page_height < 2000:
                                raise Exception()
                            break

                        page_height = page.evaluate('(window.innerHeight + window.scrollY)')
                        h: list = [15000, 15500, 16000, 16500, 17000, 17500, 18000, 18500, 19000, 19500, 20000, 20500]
                        page.mouse.wheel(0, random.choice(h))

                        t: list = [4, 4.5, 5, 5.5, 6.5, 7, 7.5]
                        time.sleep(random.choice(t))
                        page_height_after_scroll = page.evaluate('(window.innerHeight + window.scrollY)')

                    stdout_log.info(f"Scroll step completed.")

                    if p_comb == "?maxPrice=11500&minPrice=5500" and city == "bern":
                        stdout_log.info(f"TimeoutError")
                        raise Exception()

                    # Parse items
                    stdout_log.info(f"Parsing items started.")
                    page_content: str = page.content()
                    parsed_items_for_comb: list = parse_base_item(page_content)
                    stdout_log.info(f"Combination items len: {len(parsed_items_for_comb)}")
                    parsed_items_for_city.append(parsed_items_for_comb)
                    self.redis_client.insert_into_redis(parsed_items_for_city, key="parsed-items-for-city")

                    un_crawled_prices.remove(p_comb)
                    self.redis_client.insert_into_redis(un_crawled_prices, key="base-items-crawler-prices")

                except Exception:
                    page.close()
                    browser.close()
                    time.sleep(2)
                    playwright.stop()
                    time.sleep(5*60)
                    raise TimeoutError()

                page.close()
                time.sleep(0.5)
                browser.close()
                time.sleep(0.5)

                # call rotate proxy
                self._rotate_proxy_call()
                time.sleep(5)

            stdout_log.info(f"Items len for {city}: {len(parsed_items_for_city)}")
            file_path: str = f"facebook-{city}-{DATE}.jsonl.gz"
            file = self._make_file_obj(parsed_items_for_city, file_path)
            self.s3_conn.upload_file(file, file_path)

            un_crawled_cities.remove(city)
            self.redis_client.insert_into_redis(un_crawled_cities, key="base-items-crawler-cities")
            self.redis_client.insert_into_redis([], key="parsed-items-for-city")
            self.redis_client.insert_into_redis(PRICE_COMBINATIONS, key="base-items-crawler-prices")

        time.sleep(2)
        playwright.stop()


if __name__ == '__main__':
    redis_client.insert_into_redis(REQUIRED_CITIES, key="base-items-crawler-cities")
    redis_client.insert_into_redis(PRICE_COMBINATIONS, key="base-items-crawler-prices")
    redis_client.insert_into_redis([], key="parsed-items-for-city")
    fb_crawler = FacebookBaseItemsCrawler()
    fb_crawler.crawling_process()
