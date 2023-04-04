import time
import random
import itertools

from typing import List
from parsers import Parser
from playwright.sync_api import sync_playwright
from utils import BaseService, Proxy, stdout_log, retry, CATEGORIES
from config import CITIES_CITIES_CODE_MAP, DATE, REQUIRED_CITIES, PRICE_COMBINATIONS, MAX_PAGE_HEIGHT


class ScrollCrawler(BaseService):
    def __init__(self, proxies: List[Proxy], parser: Parser, category_to_scroll: str):
        super().__init__()
        required_cities_list = REQUIRED_CITIES.copy()
        price_combinations_list = PRICE_COMBINATIONS.copy()
        random.shuffle(required_cities_list)
        random.shuffle(price_combinations_list)

        stdout_log.info(required_cities_list)
        stdout_log.info(price_combinations_list)
        stdout_log.info(category_to_scroll)

        self.parser = parser
        self.required_cities = required_cities_list
        self.price_combinations = PRICE_COMBINATIONS
        self.max_page_height = MAX_PAGE_HEIGHT
        self.cat_to_scroll = category_to_scroll
        self.redis_key_for_cities = f"{category_to_scroll}-scroll-cities"
        self.redis_key_for_prices = f"{category_to_scroll}-scroll-prices"
        self.redis_key_for_items_for_city = f"{category_to_scroll}-scroll-items-for-city"
        self.redis_client.insert_into_redis(required_cities_list, key=self.redis_key_for_cities)
        self.redis_client.insert_into_redis(price_combinations_list, key=self.redis_key_for_prices)
        self.redis_client.insert_into_redis([], key=self.redis_key_for_items_for_city)
        self.proxies = proxies

    @retry(TimeoutError, stdout_log, tries=10)
    def scrolling_process(self):
        redis_required_cities: list = self.redis_client.get_mappings(key=self.redis_key_for_cities)
        if redis_required_cities:
            self.required_cities = redis_required_cities

        # Init playwright.
        playwright = sync_playwright().start()

        un_crawled_cities: list = self.required_cities.copy()
        for city in self.required_cities:
            redis_required_prices: list = self.redis_client.get_mappings(key=self.redis_key_for_prices)
            if redis_required_prices:
                self.price_combinations = redis_required_prices

            redis_parsed_items_for_city: list = self.redis_client.get_mappings(key=self.redis_key_for_items_for_city)
            _parsed_items_for_city: List[list] = redis_parsed_items_for_city if redis_parsed_items_for_city else []

            city_code: str = CITIES_CITIES_CODE_MAP[city]
            un_crawled_prices: list = self.price_combinations.copy()

            proxy_list_len = len(self.proxies) - 1
            proxy_switch = 0
            for p_comb in self.price_combinations:
                # Init browser and page per price combination.
                stdout_log.info(f"proxy: {self.proxies[proxy_switch].server}")
                browser = playwright.firefox.launch(headless=True, proxy={
                    "server": self.proxies[proxy_switch].server,
                    "username": self.proxies[proxy_switch].username,
                    "password": self.proxies[proxy_switch].password
                    })
                page = browser.new_page()

                try:
                    if self.cat_to_scroll == CATEGORIES.VEHICLE:
                        start_url: str = f"https://www.facebook.com/marketplace/{city_code}"
                    else:
                        start_url: str = f"https://www.facebook.com/marketplace/{city_code}/{self.cat_to_scroll}/{p_comb}"

                    stdout_log.info(f"City: {city}")
                    stdout_log.info(f"PAGE GOING TO: {start_url}")
                    page.goto(start_url, wait_until="load", timeout=90000)
                    time.sleep(5)

                    # Allow essential cookies step.
                    page.click("span:text('Only allow essential cookies')")
                    time.sleep(2)
                    stdout_log.info("Essential cookies step completed.")
                    stdout_log.info(f"PAGE ON URL: {page.url}")

                    if self.cat_to_scroll == CATEGORIES.VEHICLE:
                        prices = p_comb.split("=")
                        min_price = prices[0]
                        max_price = prices[1]
                        page.click("span:text('Vehicles')")
                        time.sleep(2)
                        page.fill('[placeholder="Min"]', min_price)
                        time.sleep(2)
                        page.fill('[placeholder="Max"]', max_price)
                        time.sleep(2)
                        page.click("span:text('Shop by category')")
                        time.sleep(5)
                    elif self.cat_to_scroll in [CATEGORIES.PROPERTY_FOR_RENT, CATEGORIES.PROPERTY_FOR_SALE]:
                        page.mouse.move(600, 0)
                        stdout_log.info(f"{self.cat_to_scroll} and mouse is moved to the right to be able to scroll.")

                    # Scroll step.
                    page_height_after_scroll: int = 0
                    page_height: int = 1
                    while True:
                        if page_height == page_height_after_scroll:
                            stdout_log.info("Same page height before and after scroll stopped scrolling!")
                            stdout_log.info(f"Page height {page_height}")
                            time.sleep(1)
                            break

                        if page_height > self.max_page_height:
                            stdout_log.info(f"Max page height {self.max_page_height} stopped scrolling!")
                            break

                        page_height = page.evaluate('(window.innerHeight + window.scrollY)')
                        page.mouse.wheel(0, random.choice(self.page_height_scroll_pool))
                        time.sleep(random.choice(self.page_timeout_scroll_pool))
                        page_height_after_scroll = page.evaluate('(window.innerHeight + window.scrollY)')

                    stdout_log.info(f"Scroll step completed.")

                    # Parse partial records.
                    stdout_log.info(f"Parsing {self.cat_to_scroll} partial records  started.")
                    parsed_items_for_comb: list = self.parser.parse_scrolled_records(page.content())
                    stdout_log.info(f"Found {self.cat_to_scroll} in combination {p_comb}: {len(parsed_items_for_comb)}")
                    _parsed_items_for_city.append(parsed_items_for_comb)
                    self.redis_client.insert_into_redis(_parsed_items_for_city, key=self.redis_key_for_items_for_city)

                    un_crawled_prices.remove(p_comb)
                    self.redis_client.insert_into_redis(un_crawled_prices, key=self.redis_key_for_prices)

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
                self.proxies[proxy_switch].rotate_proxy_call()
                if proxy_switch == proxy_list_len:
                    proxy_switch = 0
                else:
                    proxy_switch += 1
                time.sleep(5)

            parsed_items_for_city: list = list(itertools.chain.from_iterable(_parsed_items_for_city))
            stdout_log.info(f"Found {self.cat_to_scroll} for {city}: {len(parsed_items_for_city)}")

            file_path: str = f"facebook-{self.cat_to_scroll}-{city}-{DATE}.jsonl.gz"
            self._create_and_upload_file(file_path, parsed_items_for_city, per_city=True)

            un_crawled_cities.remove(city)
            self.redis_client.insert_into_redis(un_crawled_cities, key=self.redis_key_for_cities)
            self.redis_client.insert_into_redis([], key=self.redis_key_for_items_for_city)
            self.redis_client.insert_into_redis(PRICE_COMBINATIONS, key=self.redis_key_for_prices)

        time.sleep(2)
        playwright.stop()
