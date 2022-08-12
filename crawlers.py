import gzip
import json
import boto3
import time


from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from datetime import datetime
from config import CITIES_MAP, REQUIRED_RANGES_IN_KM, S3_PREFIX, S3_BUCKET, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
from logger import stdout_log


class FacebookCarCrawler:
    def __init__(self, required_city: str, fb_bot_email: str, fb_bot_pass: str, strict_scroll: str):
        self.cities_map = CITIES_MAP
        self.s3 = boto3.client('s3',
                               aws_access_key_id=AWS_ACCESS_KEY_ID,
                               aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        self.required_city = required_city
        self.strict_scroll = True if int(strict_scroll) else False
        self.fb_bot_email = fb_bot_email
        self.fb_bot_pass = fb_bot_pass

    @staticmethod
    def _parse_items(page_content: str):
        soup = BeautifulSoup(page_content, 'html.parser')
        raw_items: list = soup.select(
            "div.b3onmgus.ph5uu5jm.g5gj957u.buofh1pr.cbu4d94t.rj1gh0hx.j83agx80.rq0escxv.fnqts5cd"
            ".fo9g3nie.n1dktuyu.e5nlhep0.ecm0bbzt")

        parsed_items: list = []
        for item in raw_items:
            try:
                item_url_tag = item.find('a')
                item_url_raw = item_url_tag['href'] if item_url_tag else None
                item_url_splited = item_url_raw.split("/?ref")
                item_url = item_url_splited[0].strip()
                item_id = item_url.split("item/")[1].strip()

                item_data: list = item.select('div.aahdfvyu.fsotbgu8')
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
    def _make_file_obj(parsed_items: list, file: str):
        with gzip.open(file, "wb") as writer:
            for item in parsed_items:
                json_str = json.dumps(item) + "\n"
                json_bytes = json_str.encode('utf-8')
                writer.write(json_bytes)

        writer.close()
        stdout_log.info("File object made.")
        return file

    def _upload_file_obj_to_s3(self, file_obj):
        self.s3.upload_file(file_obj, S3_BUCKET, f'{S3_PREFIX}/{file_obj}')
        stdout_log.info(f"File uploaded on s3. {S3_BUCKET}/{S3_PREFIX}/{file_obj}")

    def crawling_process(self):
        # Init browser, page and login step
        stdout_log.info("Init step started.")
        playwright = sync_playwright().start()
        browser = playwright.firefox.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.facebook.com/")
        time.sleep(5)
        stdout_log.info("Init step completed.")

        # Log in step
        stdout_log.info("Log in step started.")
        page.fill("#email", self.fb_bot_email)
        time.sleep(3)
        page.fill("#pass", self.fb_bot_pass)
        time.sleep(3)
        page.click("button:text('Log In')")
        time.sleep(30)
        stdout_log.info("Log in step completed.")

        # Choose category step
        stdout_log.info("Choose category step started.")
        try:
            page.click("span:text('Marketplace')")
        except Exception as e:
            stdout_log.info("No Marketplace button.", e)
        finally:
            try:
                page.goto("https://www.facebook.com/marketplace")
            except Exception as e:
                stdout_log.info("Marketplace url unreachable", e)

        time.sleep(15)
        page.click("span:text('Vehicles')")
        time.sleep(10)
        page.click("span:text('Cars')")
        time.sleep(10)
        stdout_log.info("Choose category step completed.")

        # Crawling listings per km range
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
            required_city: str = CITIES_MAP[self.required_city]
            if previous_search_city != required_city:
                stdout_log.info("Change city in search params if it is different from required step.")
                if 'kilometres' in previous_search_km_range:
                    page.click('span:text("kilometres")')
                else:
                    page.click('span:text("kilometre")')
                time.sleep(5)

                page.fill("span:text('Location') + input", required_city)  # hardcoded
                time.sleep(5)
                page.locator(f'ul li span:text("{required_city}") >> nth=0').click()
                time.sleep(5)

                page.click('span:text("Change location")')
                time.sleep(5)
                page.click('span:text("Apply")')
                time.sleep(10)

            # Make starting point search to be from 1 km radius
            is_1km_range = False
            if 'kilometres' in previous_search_km_range and km_range == 1:
                stdout_log.info("Make starting point search to be from 1 km radius step.")
                if 'kilometres' in previous_search_km_range:
                    page.click('span:text("kilometres")')
                else:
                    page.click('span:text("kilometre")')
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
                    page.click('span:text("kilometres")')
                else:
                    page.click('span:text("kilometre")')
                time.sleep(2)

                page.click(
                    f'{locator_for_km_range} >> nth={"1" if helper_locator_for_km_range == "kilometre" or km_range > 2 else "0"}')
                time.sleep(5)

                page.click(
                    f'span:text("{km_range} {helper_locator_for_km_range if km_range < 2 else "kilometres"}") >> nth=0')
                time.sleep(5)

                page.click('span:text("Apply")')
                time.sleep(15)

            # Scroll step.
            stdout_log.info(f"Scroll step for {km_range}km range started.")
            # page_height_after_scroll = 0
            # page_height = 1
            # while True:
            #     stdout_log.info(f"Page height {page_height}")
            #     if self.strict_scroll and len(BeautifulSoup(page.content(), 'html.parser').select(
            #             "div.l9j0dhe7.f9o22wc5.ad2k81qe")) > 1:
            #         page.mouse.wheel(0, 15000)
            #         break
            #
            #     if page_height == page_height_after_scroll:
            #         break
            #
            #     page_height = page.evaluate('(window.innerHeight + window.scrollY)')
            #     page.mouse.wheel(0, 15000)
            #     time.sleep(5)
            #     page_height_after_scroll = page.evaluate('(window.innerHeight + window.scrollY)')

            stdout_log.info(f"Scroll step for {km_range}km range completed.")

            # Parse items
            # stdout_log.info(f"Parsing items step for {km_range}km range started.")
            # page_content: str = page.content()
            # parsed_items: list = self._parse_items(page_content)
            # stdout_log.info(f"Parsing items step for {km_range}km range completed.")
            #
            # if self.strict_scroll:
            #     file_path: str = f"test-facebook-{self.required_city}-strict-range-{km_range}-km-{str(datetime.now().date())}.jsonl.gz"
            # else:
            #     file_path: str = f"test-facebook-{self.required_city}-range-{km_range}-km-{str(datetime.now().date())}.jsonl.gz"
            #
            # file = self._make_file_obj(parsed_items, file_path)
            # self._upload_file_obj_to_s3(file)
            #
            # stdout_log.info(f"Crawling listings for {km_range}km range completed.")
            # time.sleep(5)

        time.sleep(5)

        page.close()
        browser.close()
        time.sleep(2)
        playwright.stop()

