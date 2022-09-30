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
    raw_items_selector: str = "div.lcfup58g.fzd7ma4j.i15ihif8.cgu29s5g.cqf1kptm.jg3vgc78.alzwoclg.bdao358l.p2pkoip2" \
                              ".qez6140x.r0bj8g6i.o9wcebwi.d2hqwtrz"
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
            item_data_selector: str = "div.i0rxk2l3.d2v05h0u"
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


def parse_car(page_content: str, base_item: dict, see_more=False) -> Union[dict, None]:
    soup: BeautifulSoup = BeautifulSoup(page_content, 'html.parser')
    _title = soup.select_one("div.gt60zsk1.rl78xhln.r227ecj6.g4qalytl span.gvxzyvdx.aeinzg81.t7p7dqev.gh25dzvf"
                             ".tb6i94ri.gupuyl1y.i2onq4tn.b6ax4al1.gem102v4.ncib64c9.mrvwc6qr.sx8pxkcf.f597kf1v"
                             ".cpcgwwas.bx1hu7np.ib8x7mpr.qntmu8s7.tq4zoyjo.o48pnaf2.pbevjfx6")
    if _title:
        title = _title.text
        if "Sold" in title:
            del soup
            return
    else:
        del soup
        return

    seller = parse_seller(page_content)
    if not seller:
        return

    _publish_time = soup.select_one("div.gt60zsk1.rl78xhln.r227ecj6.g4qalytl span.gvxzyvdx.aeinzg81.t7p7dqev.gh25dzvf"
                                    ".tb6i94ri.gupuyl1y.i2onq4tn.b6ax4al1.gem102v4.ncib64c9.mrvwc6qr.sx8pxkcf.f597kf1v"
                                    ".cpcgwwas.f5mw3jnl.szxhu1pg.nfkogyam.kkmhubc1.tes86rjd.rtxb060y")

    publish_time: str = _publish_time.text if _publish_time else None
    _description = soup.select_one("div.n3t5jt4f.nch0832m.rj2hsocd.oxkhqvkx.s1m0hq7j span.gvxzyvdx.aeinzg81.t7p7dqev"
                                   ".gh25dzvf.tb6i94ri.gupuyl1y.i2onq4tn.b6ax4al1.gem102v4.ncib64c9.mrvwc6qr.sx8pxkcf"
                                   ".f597kf1v.cpcgwwas.m2nijcs8.hxfwr5lz.k1z55t6l.oog5qr5w.tes86rjd.pbevjfx6")
    description = None
    if _description:
        description = _description.text
        if see_more:
            description = description.replace("See less", "")

    _images = soup.select("img.pytsy3co.p9wrh9lq.mfclru0v")
    images = [image.get('src') for image in _images][1:] if _images else None
    del soup

    return Car(**base_item, title=title, publish_time=publish_time,
               description=description, seller=seller, images=images).dict()
