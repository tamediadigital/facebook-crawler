import gzip
import itertools
import json
import time

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from iteration_utilities import unique_everseen
from config import CITIES_MAP, REQUIRED_RANGES_IN_KM, DATE
from logger import stdout_log
from retry_handler import retry
from redis_db import redis_client
from typing import List
from s3_conn import s3_conn


class FacebookCarCrawler:
    def __init__(self, required_cities: list, fb_bot_email: str, fb_bot_pass: str, scroll_height: int):
        self.cities_map = CITIES_MAP
        self.s3_conn = s3_conn
        self.required_cities = required_cities
        self.fb_bot_email = fb_bot_email
        self.fb_bot_pass = fb_bot_pass
        self.redis_client = redis_client
        self.scroll_height = scroll_height

    @staticmethod
    def _parse_items(page_content: str):
        soup = BeautifulSoup(page_content, 'html.parser')
        # TODO: raw_items css selector will change over the time
        raw_items: list = soup.select(
            "div.lcfup58g.fzd7ma4j.i15ihif8.cgu29s5g.cqf1kptm.jg3vgc78.alzwoclg.bdao358l.p2pkoip2.qez6140x.r0bj8g6i.o9wcebwi.d2hqwtrz")

        parsed_items: list = []
        for item in raw_items:
            try:
                item_url_tag = item.find('a')
                item_url_raw = item_url_tag['href'] if item_url_tag else None
                item_url_splited = item_url_raw.split("/?ref")
                item_url = item_url_splited[0].strip()
                item_id = item_url.split("item/")[1].strip()

                # TODO: item_data css selector will change over the time
                item_data: list = item.select('div.i0rxk2l3.d2v05h0u')
                if not item_data:
                    continue

                item_price: str = item_data[0].text
                item_short_desc: str = item_data[1].text if item_data[1].text else None
                item_location: str = item_data[2].text
                item_splited_location: list = item_location.split(',')
                item_city: str = item_splited_location[0]
                item_canton_code: str = item_splited_location[1].strip()
                item_mileage: str = item_data[3].text if item_data[3].text else None

                parsed_items.append({
                                        "item_id": item_id,
                                        "item_url": item_url,
                                        "item_price": item_price,
                                        "item_short_desc": item_short_desc,
                                        "item_location": item_location,
                                        "item_city": item_city,
                                        "item_canton_code": item_canton_code,
                                        "item_mileage": item_mileage
                                        })
            except IndexError as e:
                stdout_log.error(e)
                continue
            except AttributeError as e:
                stdout_log.error(e)
                continue

        return parsed_items

    @staticmethod
    def _make_file_obj(parsed_items_for_city: List[list], file: str):
        chained_list_of_items: list = list(unique_everseen(list(itertools.chain.from_iterable(parsed_items_for_city))))
        with gzip.open(file, "wb") as writer:
            for item in chained_list_of_items:
                json_str = json.dumps(item) + "\n"
                json_bytes = json_str.encode('utf-8')
                writer.write(json_bytes)

        writer.close()
        stdout_log.info("File object made.")
        return file

    @retry(TimeoutError, stdout_log)
    def crawling_process(self):
        redis_required_cities: list = self.redis_client.get_mappings()
        if redis_required_cities:
            self.required_cities = redis_required_cities

        # Init browser, page and login step
        stdout_log.info("Init step started.")
        playwright = sync_playwright().start()
        browser = playwright.firefox.launch(headless=True, timeout=60000)
        page = browser.new_page()
        page.goto("https://www.facebook.com/")
        time.sleep(5)
        stdout_log.info("Init step completed.")

        # Allow essential cookies step
        try:
            page.click("button:text('Only allow essential cookies')")
            time.sleep(5)
            stdout_log.info("Essential cookies step completed.")
        except TimeoutError as e:
            stdout_log.info(f"Button to allow essential cookies not found! {e}",)

        # Log in step
        stdout_log.info("Log in step started.")
        page.fill("#email", self.fb_bot_email)
        time.sleep(5)

        page.fill("#pass", self.fb_bot_pass)
        time.sleep(5)

        page.click("button:text('Log In')")
        time.sleep(20)
        stdout_log.info("Log in step completed.")

        # Choose category step
        stdout_log.info("Choose category step started.")
        try:
            page.click("span:text('Marketplace')")
        except Exception as e:
            stdout_log.info("No Marketplace button.", e)
        finally:
            page.goto("https://www.facebook.com/marketplace")

        time.sleep(10)
        page.click("span:text('Vehicles')")
        time.sleep(10)
        page.click("span:text('Cars')")
        time.sleep(10)

        stdout_log.info("Choose category step completed.")

        uncrawled_cities: list = self.required_cities.copy()
        for city in self.required_cities:
            parsed_items_for_city: list = []
            try:
                # Crawling listings per km range
                stdout_log.info(f"Scroll for {city} ranges started.")
                stdout_log.info("Crawling listings per km range step started.")
                for idx, km_range in enumerate(REQUIRED_RANGES_IN_KM):
                    stdout_log.info(f"Crawling listings for {km_range}km range started.")
                    if idx in [0, 1]:
                        helper_locator_for_km_range = "kilometre"
                        locator_for_km_range = 'span:text("kilometre")'
                    else:
                        helper_locator_for_km_range = "kilometres"
                        locator_for_km_range = 'span:text("kilometres")'

                    # Detect previous search params
                    previous_radius_filter_text = page.locator('div#seo_filters').text_content()
                    previous_radius_filter_split_text: list = previous_radius_filter_text.split(' · ')
                    previous_search_city: str = previous_radius_filter_split_text[0].strip()
                    previous_search_km_range: str = previous_radius_filter_split_text[1].strip()

                    # Change city in search params if it is different from required
                    required_city: str = CITIES_MAP[city]
                    if previous_search_city != required_city:
                        stdout_log.info("Change city in search params if it is different from required step.")
                        if 'kilometres' in previous_search_km_range:
                            page.locator('span:text("kilometres") >> nth=0').click()
                        else:
                            page.locator('span:text("kilometre") >> nth=0').click()
                        time.sleep(5)

                        page.fill("span:text('Location') + input", required_city)  # hardcoded
                        time.sleep(5)
                        page.locator(f'ul li span:text("{required_city}") >> nth=0').click()
                        time.sleep(5)

                        page.locator('span:text("Change location")').click()
                        time.sleep(5)
                        page.locator('span:text("Apply")').click()
                        time.sleep(10)

                    # Make starting point search to be from 1 km radius
                    is_1km_range = False
                    if 'kilometres' in previous_search_km_range and km_range == 1:
                        stdout_log.info("Make starting point search to be from 1 km radius step.")
                        if 'kilometres' in previous_search_km_range:
                            page.click('span:text("kilometres") >> nth=0')
                        else:
                            page.click('span:text("kilometre") >> nth=0')
                        time.sleep(5)

                        page.click('span:text("kilometres") >> nth=1')
                        time.sleep(2)
                        page.click('span:text("1 kilometre")')
                        time.sleep(2)
                        page.click('span:text("Apply")')
                        time.sleep(10)
                        is_1km_range = True
                    elif '1 kilometre' in previous_search_km_range:
                        is_1km_range = True

                    # Step for changing km radius param for search.
                    # note: It starts from 1 km range so there is no point for setting it ones again to be 1 km.
                    if is_1km_range and km_range == 1:
                        pass
                    else:
                        if 'kilometres' in previous_search_km_range:
                            page.click('span:text("kilometres") >> nth=0')
                        else:
                            page.click('span:text("kilometre") >> nth=0')
                        time.sleep(7)

                        page.locator("span:text('Radius') + div").click()
                        time.sleep(5)
                        stdout_log.info("Line 224 span:text('Radius') + div completed")

                        page.locator(
                            f'span:text("{km_range} {helper_locator_for_km_range if int(km_range) < 2 else "kilometres"}") >> nth=0').click()
                        time.sleep(5)
                        stdout_log.info(f'Line 228 span:text("{km_range} {helper_locator_for_km_range if int(km_range) < 2 else "kilometres"}") >> nth=0 + div completed')

                        page.locator('span:text("Apply")').click()
                        time.sleep(10)

                    # Scroll step.
                    stdout_log.info(f"Scroll step for {km_range}km range started.")
                    page_height_after_scroll = 0
                    page_height = 1
                    while True:
                        stdout_log.info(f"Page height {page_height}")
                        results_from_outside_your_search = BeautifulSoup(page.content(), 'html.parser').select(
                            "div.nch0832m.ez8dtbzv.oxkhqvkx.g4qalytl.eo2axi11.p8zq7ayg.i7rjuzed.pry8b2m5.q6ul9yy4")

                        if results_from_outside_your_search:
                            stdout_log.info("Results from outside your search stopped scrolling!")
                            break
                        del results_from_outside_your_search

                        if page_height_after_scroll > self.scroll_height:
                            stdout_log.info(f"Page height bigger than {self.scroll_height} stopped scrolling!")
                            break

                        if page_height == page_height_after_scroll:
                            stdout_log.info("Same page height before and after scroll stopped scrolling!")
                            break

                        page_height = page.evaluate('(window.innerHeight + window.scrollY)')
                        page.mouse.wheel(0, 20000)
                        time.sleep(5)
                        page_height_after_scroll = page.evaluate('(window.innerHeight + window.scrollY)')

                    stdout_log.info(f"Scroll step for {km_range}km range completed.")

                    # Parse items
                    stdout_log.info(f"Parsing items step for {km_range}km range started.")
                    page_content: str = page.content()
                    parsed_items: list = self._parse_items(page_content)
                    parsed_items_for_city.append(parsed_items)
                    stdout_log.info(f"Parsing items step for {km_range}km range completed.")
                    stdout_log.info(f"Crawling listings for {km_range}km range completed.")
                    time.sleep(7)

                file_path: str = f"test-facebook-{city}-{DATE}.jsonl.gz"
                file = self._make_file_obj(parsed_items_for_city, file_path)
                self.s3_conn.upload_file(file, file_path)

                uncrawled_cities.remove(city)
                self.redis_client.insert_into_redis(uncrawled_cities)
                time.sleep(5)
            except TimeoutError:
                page.close()
                browser.close()
                time.sleep(2)
                playwright.stop()
                raise TimeoutError()

        page.close()
        browser.close()
        time.sleep(2)
        playwright.stop()
