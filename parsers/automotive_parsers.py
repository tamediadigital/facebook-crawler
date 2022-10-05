import json
import re
from typing import List, Union
from bs4 import BeautifulSoup
from utils.logger import stdout_log
from parsers.base_parsers import parse_seller
from schemas.automotive_schemas.car_schemas import PartialCar, Car


def parse_partial_cars(page_content: str) -> List[dict]:
    """This func takes as input page content, locates cars on the page,
    collects data and parse it as list of PartialCar."""
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
            stdout_log.error(e)
            continue
        except AttributeError as e:
            stdout_log.error(e)
            continue

        try:
            item_data_selector: str = "div.x1gslohp.xkh6y0r"
            item_data: list = item.select(item_data_selector)
            if not item_data:
                continue

            price: str = item_data[0].text
            short_desc: str = item_data[1].text if item_data[1].text else None

            item_location: str = item_data[2].text
            item_location_splited: list = item_location.split(',')
            city: str = item_location_splited[0]
            canton_code: str = item_location_splited[1].strip()
            mileage: str = item_data[3].text if item_data[3].text else None
        except IndexError as e:
            stdout_log.error(e)
            continue
        except AttributeError as e:
            stdout_log.error(e)
            continue

        parsed_items.append(PartialCar(ad_id=_id, url=url, price=price, city=city, canton_code=canton_code,
                                       short_desc=short_desc, mileage=mileage).dict())

    return parsed_items


def parse_car_css(page_content: str, base_item: dict, see_more=False) -> Union[dict, None]:
    soup: BeautifulSoup = BeautifulSoup(page_content, 'html.parser')
    _title = soup.select_one("div.x1swvt13.x18d9i69.x1pi30zi.xyamay9 span.x193iq5w.xeuugli.x13faqbe.x1vvkbs.xlh3980."
                             "xvmahel.x1n0sxbx.x1lliihq.x1s928wv.xhkezso.x1gmr53x.x1cpjm7i.x1fgarty.x1943h6x.xtoi2st."
                             "x41vudc.xngnso2.x1qb5hxa.x1xlr1w8.xzsf02u")
    if _title:
        title = _title.text
        if "Sold" in title:
            del soup
            stdout_log.info("Return sold")
            return
    else:
        del soup
        stdout_log.info("Return no title")
        return

    seller = parse_seller(page_content)
    if not seller:
        stdout_log.info("Return no seller")
        return

    _publish_time = soup.select_one("div.x1swvt13.x18d9i69.x1pi30zi.xyamay9 span.x193iq5w.xeuugli.x13faqbe.x1vvkbs"
                                    ".xlh3980.xvmahel.x1n0sxbx.x1lliihq.x1s928wv.xhkezso.x1gmr53x.x1cpjm7i.x1fgarty"
                                    ".x1943h6x.x4zkp8e.x676frb.x1nxh6w3.x1sibtaa.xo1l8bm.xi81zsa")

    publish_time: str = _publish_time.text if _publish_time else None
    _description = soup.select_one("div.x126k92a.xkhd6sd.xsag5q8.x4uap5.xz9dl7a span.x193iq5w.xeuugli.x13faqbe.x1vvkbs."
                                   "xlh3980.xvmahel.x1n0sxbx.x1lliihq.x1s928wv.xhkezso.x1gmr53x.x1cpjm7i.x1fgarty"
                                   ".x1943h6x.xudqn12.x3x7a5m.x6prxxf.xvq8zen.xo1l8bm.xzsf02u")
    description = None
    if _description:
        description = _description.text
        if see_more:
            description = description.replace("See less", "")

    _images = soup.select("img.x5yr21d.xl1xv1r.xh8yej3")
    if len(_images) <= 1:
        images = [image.get('src') for image in _images] if _images else None
    else:
        images = [image.get('src') for image in _images][1:] if _images else None
    del soup

    return Car(**base_item, title=title, publish_time=publish_time,
               description=description, seller=seller, images=images).dict()


def parse_car_regex(page_content: str, base_item: dict) -> Union[dict, None]:
    _title = re.search('"marketplace_listing_title":"(.*)","condition":', page_content)
    if _title:
        title = _title.group(1)
        if "Sold" in title:
            stdout_log.info("Listing is Sold!")
            return
    else:
        stdout_log.info("No title data, invalid listing!")
        return

    seller = parse_seller(page_content)
    if not seller:
        stdout_log.info("No seller data, invalid listing!")
        return

    _publish_time = re.search('Listed <!-- -->(.*)<!-- --> in', page_content)
    stdout_log.info(f"{_publish_time}")
    publish_time: str = _publish_time.group(1) if _publish_time else None

    _description = re.search('"redacted_description":{"text":"(.*)"},"creation_time"', page_content)
    description: str = _description.group(1) if _description else None

    try:
        _images = re.search('"listing_photos":(.*),"pre_recorded_videos"', page_content)
        images = [i["image"]["uri"] for i in json.loads(_images.group(1))] if _images else None
    except KeyError as e:
        stdout_log.error(e)
        images = None

    return Car(**base_item, title=title, publish_time=publish_time,
               description=description, seller=seller, images=images).dict()
