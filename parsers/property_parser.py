import json
import re

from datetime import datetime, timedelta
from parsers.base_parser import Parser
from schemas.property_schemas import PropertyForSale, PropertyForRent


class PropertyParser(Parser):

    @staticmethod
    def _parse_available_from(availability_string: str):
        time_period = 0
        time_period_multiplayer = 0
        if "day" in availability_string:
            time_period = 1
            time_period_multiplayer = 1
        elif "days" in availability_string:
            time_period = 1
            time_period_multiplayer = 1
            try:
                time_period_multiplayer = re.findall(r'\d+', availability_string)[0]
            except IndexError:
                pass
        elif "week" in availability_string:
            time_period = 7
            time_period_multiplayer = 1
        elif "weeks" in availability_string:
            time_period = 7
            time_period_multiplayer = 1
            try:
                time_period_multiplayer = re.findall(r'\d+', availability_string)[0]
            except IndexError:
                pass
        elif "month" in availability_string:
            time_period = 30
            time_period_multiplayer = 1
        elif "months" in availability_string:
            time_period = 30
            time_period_multiplayer = 1
            try:
                time_period_multiplayer = re.findall(r'\d+', availability_string)[0]
            except IndexError:
                pass

        return str(datetime.now() - timedelta(days=time_period * time_period_multiplayer))

    def _parse_pdp_fields(self, page_content: str):
        _raw_pdp_fields: str = self._regex_search_between(page_content, '"pdp_display_sections":', ',"marketplace_listing_category"')
        if not _raw_pdp_fields:
            return
        pdp_fields = {}
        raw_pdp_fields = json.loads(_raw_pdp_fields)
        for dict_0 in raw_pdp_fields:
            for k_0, v_0 in dict_0.items():
                if k_0 == "pdp_fields":
                    for dict_1 in v_0:
                        pdp_fields[dict_1['icon_name']] = dict_1['display_label']
        return pdp_fields

    def parse_item(self, page_content, scroll_record, category: str) -> dict:
        if category == "propertyrentals":
            record = PropertyForRent(**scroll_record)
        else:
            record = PropertyForSale(**scroll_record)

        record.title = self._parse_title(page_content, ad_id=scroll_record['adId'])
        record.description = self._parse_description(page_content)
        record.imageLinks = self._parse_image_links(page_content)
        record.isBoosted = self._parse_is_boosted(page_content)

        if self._parse_seller(page_content):
            seller_id, seller_type = self._parse_seller(page_content)
            record.sellerId = seller_id
            record.sellerType = seller_type

        pdp_fields = self._parse_pdp_fields(page_content)
        if not pdp_fields:
            return record.dict()

        bedrooms_bathrooms = pdp_fields.get('bedrooms-bathrooms')
        if bedrooms_bathrooms:
            try:
                bedrooms = bedrooms_bathrooms.split('·')[0].strip()
                record.rooms = bedrooms

                bathrooms = bedrooms_bathrooms.split('·')[1].strip()
                record.bathrooms = bathrooms
            except IndexError:
                pass

        property_type = pdp_fields.get('building-city')
        if property_type:
            record.propertyType = property_type.lower()

        parking = pdp_fields.get('car')
        if parking:
            record.parking = parking.lower()

        address = pdp_fields.get('pin')
        if address:
            record.address = address

        living_space = pdp_fields.get('borders')
        if living_space:
            record.livingSpace = living_space

        available_from = pdp_fields.get('clock')
        if available_from:
            record.availableFrom = self._parse_available_from(available_from)

        return record.dict()
