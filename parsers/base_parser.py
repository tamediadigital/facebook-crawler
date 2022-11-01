import json
import re

from abc import ABC
from typing import List
from utils import stdout_log


class Parser(ABC):
    @staticmethod
    def parse_scrolled_records(page_content: str) -> List[dict]:
        pass

    def parse_item(self, page_content: str, scroll_item: dict, category: str) -> dict:
        pass

    @staticmethod
    def _regex_search_between(page_content: str, first_pair: str, second_pair: str):
        result = re.search(f'{first_pair}(.*){second_pair}', page_content)
        if not result:
            return
        return result.group(1)

    def _parse_title(self, page_content: str):
        title: str = self._regex_search_between(page_content, '"marketplace_listing_title":"', '","condition"') or \
                     self._regex_search_between(page_content, '"marketplace_listing_title":"', '","inventory_count"') or \
                     self._regex_search_between(page_content, '"marketplace_listing_title":"', '","is_pending"') or \
                     self._regex_search_between(page_content, '"marketplace_listing_title":"', '","is_live"')
        if not title:
            return

        if "Sold" in title:
            stdout_log.info("Listing is Sold!")
            return
        return title

    def _parse_description(self, page_content: str):
        description: str = self._regex_search_between(page_content, '"redacted_description":{"text":"', '"},"creation_time"')
        return description

    def _parse_seller(self, page_content: str):
        res = self._regex_search_between(page_content, '"actors":', ',"__isEntity"')
        try:
            seller_data = json.loads(res)
            seller_id = seller_data[0]["id"]
            seller_name = seller_data[0]["name"]
            seller_type = seller_data[0]["__typename"]
        except [IndexError, KeyError]:
            return
        return seller_id, seller_name, seller_type

    def _parse_image_links(self, page_content: str):
        res = self._regex_search_between(page_content, '"listing_photos":', ',"pre_recorded_videos"')
        if res == "null" or res is None:
            return

        image_links = [image['image']['uri'] for image in json.loads(res)]
        return image_links

    def _parse_is_boosted(self, page_content: str):
        _is_boosted = self._regex_search_between(page_content, '"boosted_marketplace_listing":', ',"promoted_listing"')
        is_boosted = _is_boosted.replace('"', '').lower() if _is_boosted != "null" and _is_boosted is not None else None
        return is_boosted
