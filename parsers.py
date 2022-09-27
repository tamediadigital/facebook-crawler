from typing import List

from bs4 import BeautifulSoup
from logger import stdout_log
from schemas import BaseItem


def parse_base_item(page_content: str) -> List[dict]:
    """This func takes as input page content, locates items on the page, collects data and parse it as items."""
    # TODO: CSS selectors will change over the time!

    soup: BeautifulSoup = BeautifulSoup(page_content, 'html.parser')
    raw_items_selector: str = "div.lcfup58g.fzd7ma4j.i15ihif8.cgu29s5g.cqf1kptm.jg3vgc78.alzwoclg.bdao358l.p2pkoip2" \
                              ".qez6140x.r0bj8g6i.o9wcebwi.d2hqwtrz"
    raw_items: list = soup.select(raw_items_selector)
    stdout_log.info(f"raw_items len: {len(raw_items)}")

    parsed_items: list = []
    for item in raw_items:
        try:
            item_url_tag = item.find('a')
            if not item_url_tag:
                continue
            item_url_raw: str = item_url_tag['href']
            item_url_splited: list = item_url_raw.split("/?")
            item_url: str = item_url_splited[0].strip()
            item_id: str = item_url.split("item/")[1].strip()
        except IndexError as e:
            stdout_log.error(e)
            continue
        except AttributeError as e:
            stdout_log.error(e)
            continue

        try:
            item_data_selector: str = "div.i0rxk2l3.d2v05h0u"
            item_data: list = item.select(item_data_selector)
            if not item_data:
                continue

            item_price: str = item_data[0].text
            item_short_desc: str = item_data[1].text if item_data[1].text else None

            item_location: str = item_data[2].text
            item_location_splited: list = item_location.split(',')
            item_city: str = item_location_splited[0]
            item_canton_code: str = item_location_splited[1].strip()
            item_mileage: str = item_data[3].text if item_data[3].text else None

        except IndexError as e:
            stdout_log.error(e)
            continue
        except AttributeError as e:
            stdout_log.error(e)
            continue

        base_item: BaseItem = BaseItem(ad_id=item_id, url=item_url, price=item_price, city=item_city,
                                       canton_code=item_canton_code, short_desc=item_short_desc, mileage=item_mileage)
        parsed_items.append(base_item.dict())

    return parsed_items


def parse_detailed_item():
    pass
