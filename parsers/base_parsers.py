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
    see_more = soup.select("div.n3t5jt4f.nch0832m.rj2hsocd.oxkhqvkx.s1m0hq7j span.gvxzyvdx.aeinzg81.t7p7dqev"
                           ".gh25dzvf.tb6i94ri.gupuyl1y.i2onq4tn.k1z55t6l.oog5qr5w.innypi6y.pbevjfx6")
    del soup
    return True if see_more else False
