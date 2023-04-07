from typing import List
from bs4 import BeautifulSoup

from parsers.base_parser import Parser
from schemas import RecordFromScroll
from utils import stdout_log


class ScrollParser(Parser):

    @staticmethod
    def parse_scrolled_records(page_content: str) -> List[dict]:
        """This func takes as input page content, locates records on the page,
        collects data and parse it as list of RecordFromScroll."""
        # TODO: CSS selectors will change over the time!

        soup: BeautifulSoup = BeautifulSoup(page_content, 'html.parser')
        raw_items_selector: str = "div.x1e558r4.x150jy0e.xs83m0k.x1iyjqo2.xdt5ytf.x1r8uery.x78zum5.x9f619.x291uyu" \
                                  ".x1uepa24.xnpuxes.xjkvuk6.x1iorvi4"
        raw_items: list = soup.select(raw_items_selector)
        stdout_log.info(f"raw_items len: {len(raw_items)}")
        del soup
        parsed_items: list = []
        for item in raw_items:
            try:
                item_url_tag = item.find('a')
                if not item_url_tag:
                    continue
                item_url_raw: str = item_url_tag['href']
                item_url_splited: list = item_url_raw.split("/?")
                _item_url: str = item_url_splited[0].strip()
                url: str = f"https://www.facebook.com{_item_url}"
                _id: str = _item_url.split("item/")[1].strip()
            except IndexError as e:
                # stdout_log.error(e)
                continue
            except AttributeError as e:
                # stdout_log.error(e)
                continue

            try:
                item_data_selector: str = "div.x1gslohp.xkh6y0r"
                item_data: list = item.select(item_data_selector)
                if not item_data:
                    continue

                price: str = item_data[0].text
                item_location: str = item_data[2].text
                item_location_splited: list = item_location.split(',')
                city: str = item_location_splited[0]
                canton_code: str = item_location_splited[1].strip()
            except IndexError as e:
                # stdout_log.error(e)
                continue
            except AttributeError as e:
                # stdout_log.error(e)
                continue

            parsed_items.append(RecordFromScroll(adId=_id, url=url, price=price, city=city, cantonCode=canton_code).dict())

        return parsed_items
