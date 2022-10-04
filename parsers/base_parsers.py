import json
import re

from bs4 import BeautifulSoup
from schemas.automotive_schemas.base_automotive_schemas import Seller


def parse_seller(page_content: str):
    result = re.search('"actors":(.*),"__isEntity"', page_content)
    if not result:
        return

    res = result.group(1)
    try:
        seller_data = json.loads(res)
        seller_id = seller_data[0]["id"]
        seller_name = seller_data[0]["name"]
        seller = Seller(seller_id=seller_id, seller_name=seller_name)
    except [IndexError, KeyError]:
        return
    return seller


def is_see_more(page_content: str) -> bool:
    soup = BeautifulSoup(page_content, 'html.parser')
    see_more = soup.select("div.x126k92a.xkhd6sd.xsag5q8.x4uap5.xz9dl7a span.x193iq5w.xeuugli.x13faqbe.x1vvkbs.xlh3980"
                           ".xvmahel.x1n0sxbx.x6prxxf.xvq8zen.x1s688f.xzsf02u")
    del soup
    return True if see_more else False
