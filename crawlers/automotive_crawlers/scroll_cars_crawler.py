import itertools
import time
import random


from typing import List
from playwright.sync_api import sync_playwright
from config import CITIES_CITIES_CODE_MAP, DATE, REQUIRED_CITIES, PRICE_COMBINATIONS
from crawlers.automotive_crawlers.base_automotive_crawler import BaseCarsCrawler
from utils.logger import stdout_log
from utils.proxy import Proxy
from utils.retry_handler import retry
from parsers.automotive_parsers import parse_partial_cars


class ScrollCarsCrawler(BaseCarsCrawler):
    def __init__(self, proxy: Proxy):
        super().__init__()
        self.proxy = proxy
        self.required_cities = REQUIRED_CITIES
        self.price_combinations = PRICE_COMBINATIONS
        self.redis_client.insert_into_redis(REQUIRED_CITIES, key="scroll-crawler-cities-list")
        self.redis_client.insert_into_redis(PRICE_COMBINATIONS, key="scroll-crawler-prices-list")
        self.redis_client.insert_into_redis([], key="collected-partial-cars-for-city-list")

    @retry(TimeoutError, stdout_log)
    def scrolling_process(self):
        redis_required_cities: list = self.redis_client.get_mappings(key="scroll-crawler-cities-list")
        if redis_required_cities:
            self.required_cities = redis_required_cities

        # Init playwright.
        playwright = sync_playwright().start()

        un_crawled_cities: list = self.required_cities.copy()
        for city in self.required_cities:
            redis_required_prices: list = self.redis_client.get_mappings(key="scroll-crawler-prices-list")
            if redis_required_prices:
                self.price_combinations = redis_required_prices

            redis_parsed_items_for_city: list = self.redis_client\
                .get_mappings(key="collected-partial-cars-for-city-list")
            _parsed_items_for_city: List[list] = redis_parsed_items_for_city if redis_parsed_items_for_city else []

            city_code: str = CITIES_CITIES_CODE_MAP[city]
            un_crawled_prices: list = self.price_combinations.copy()
            for p_comb in self.price_combinations:
                # Init browser and page per price combination.
                browser = playwright.firefox.launch(headless=True, proxy={
                    "server": self.proxy.server,
                    "username": self.proxy.username,
                    "password": self.proxy.password
                    })
                page = browser.new_page()

                try:
                    start_url: str = f"https://www.facebook.com/marketplace/{city_code}/cars/{p_comb}"
                    stdout_log.info(f"City: {city}")
                    stdout_log.info(f"PAGE GOING TO: {start_url}")
                    page.goto(start_url)
                    time.sleep(5)

                    # Allow essential cookies step.
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
                        page.mouse.wheel(0, random.choice(self.page_height_scroll_pool))
                        time.sleep(random.choice(self.page_timeout_scroll_pool))
                        page_height_after_scroll = page.evaluate('(window.innerHeight + window.scrollY)')

                    stdout_log.info(f"Scroll step completed.")

                    # Parse partial cars.
                    stdout_log.info(f"Parsing cars started.")
                    parsed_items_for_comb: list = parse_partial_cars(page.content())
                    stdout_log.info(f"Found cars in combination {p_comb}: {len(parsed_items_for_comb)}")
                    _parsed_items_for_city.append(parsed_items_for_comb)
                    self.redis_client.insert_into_redis(_parsed_items_for_city,
                                                        key="collected-partial-cars-for-city-list")

                    un_crawled_prices.remove(p_comb)
                    self.redis_client.insert_into_redis(un_crawled_prices, key="scroll-crawler-prices-list")

                except Exception as e:
                    stdout_log.error(f"Error: {e}")
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

                # Call rotate proxy.
                self.proxy.rotate_proxy_call()
                time.sleep(5)

            parsed_items_for_city: list = list(itertools.chain.from_iterable(_parsed_items_for_city))
            stdout_log.info(f"Found cars for {city}: {len(parsed_items_for_city)}")

            file_path: str = f"facebook-{city}-{DATE}.jsonl.gz"
            self._create_and_upload_file(file_path, parsed_items_for_city, per_city=True)

            un_crawled_cities.remove(city)
            self.redis_client.insert_into_redis(un_crawled_cities, key="scroll-crawler-cities-list")
            self.redis_client.insert_into_redis([], key="collected-partial-cars-for-city-list")
            self.redis_client.insert_into_redis(PRICE_COMBINATIONS, key="scroll-crawler-prices-list")

        time.sleep(2)
        playwright.stop()
