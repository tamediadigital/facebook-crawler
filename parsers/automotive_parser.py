import json

from datetime import datetime
from schemas import AutomotiveRecord
from parsers.base_parser import Parser


class AutomotiveParser(Parser):
    def _parse_available_from(self, page_content: str):
        _available_from = self._regex_search_between(page_content, '"creation_time":', ',"location_text"')
        available_from = str(datetime.fromtimestamp(int(_available_from))) if _available_from else None
        return available_from

    def _parse_make(self, page_content: str):
        make = self._regex_search_between(page_content, '"vehicle_make_display_name":"', '","vehicle_model_display_name"')
        return make

    def _parse_model(self, page_content: str):
        model = self._regex_search_between(page_content, '"vehicle_model_display_name":"', '","vehicle_number_of_owners"')
        return model

    def _parse_mileage(self, page_content: str):
        _mileage = self._regex_search_between(page_content, '"vehicle_odometer_data":{"unit":null,"value":', '},"vehicle_registration_plate_information"')
        mileage = _mileage if _mileage != "null" else None
        return mileage

    def _parse_horse_power(self, page_content: str):
        res = self._regex_search_between(page_content, '"horse_power":', ',"safety_rating_front"')
        if res == "null" or res is None:
            return

        horse_power = json.loads(res).get("value")
        return horse_power

    def _parse_fuel_type(self, page_content: str):
        _fuel_type = self._regex_search_between(page_content, '"vehicle_fuel_type":"', '","vehicle_identification_number"')
        fuel_type = _fuel_type.replace('"', '').lower() if _fuel_type != "null" and _fuel_type is not None else None
        return fuel_type

    def _parse_condition(self, page_content: str):
        _condition = self._regex_search_between(page_content, '"condition":', ',"custom_title"')
        condition = _condition.replace('"', '').lower() if _condition != "null" and _condition is not None else None
        return condition

    def _parse_condition_type(self, page_content: str):
        _condition_type = self._regex_search_between(page_content, '"vehicle_condition":', ',"vehicle_exterior_color"')
        condition_type = _condition_type.replace('"', '').lower() if _condition_type != "null" and _condition_type is not None else None
        return condition_type

    def _parse_body_color(self, page_content: str):
        _vehicle_exterior_color = self._regex_search_between(page_content, '"vehicle_exterior_color":', ',"vehicle_features"')
        vehicle_exterior_color = _vehicle_exterior_color.replace('"', '').lower() if _vehicle_exterior_color != "null" and _vehicle_exterior_color is not None else None
        return vehicle_exterior_color

    def _parse_interior_color(self, page_content: str):
        _vehicle_interior_color = self._regex_search_between(page_content, '"vehicle_interior_color":', ',"vehicle_is_paid_off"')
        vehicle_interior_color = _vehicle_interior_color.replace('"', '').lower() if _vehicle_interior_color != "null" and _vehicle_interior_color is not None else None
        return vehicle_interior_color

    def _parse_transmission_type(self, page_content: str):
        _vehicle_transmission_type = self._regex_search_between(page_content, '"vehicle_transmission_type":', ',"vehicle_trim_display_name"')
        vehicle_transmission_type = _vehicle_transmission_type.replace('"', '').lower() if _vehicle_transmission_type != "null" and _vehicle_transmission_type is not None else None
        return vehicle_transmission_type

    def _parse_description(self, page_content: str):
        description: str = self._regex_search_between(page_content, '"redacted_description":{"text":"', '"},"creation_time"')
        return description

    def parse_item(self, page_content, scroll_record, category: str) -> dict:
        record = AutomotiveRecord(**scroll_record)

        record.vehicleType = category
        record.title = self._parse_title(page_content, ad_id=scroll_record['adId'])
        record.description = self._parse_description(page_content)
        record.imageLinks = self._parse_image_links(page_content)
        record.availableFrom = self._parse_available_from(page_content)
        record.isBoosted = self._parse_is_boosted(page_content)

        if self._parse_seller(page_content):
            seller_id, seller_type = self._parse_seller(page_content)
            record.sellerId = seller_id
            record.sellerType = seller_type

        record.condition = self._parse_condition(page_content)
        record.conditionType = self._parse_condition_type(page_content)
        record.mileage = self._parse_mileage(page_content)
        record.make = self._parse_make(page_content)
        record.model = self._parse_model(page_content)
        record.hp = self._parse_horse_power(page_content)
        record.fuelType = self._parse_fuel_type(page_content)
        record.bodyColor = self._parse_body_color(page_content)
        record.interiorColor = self._parse_interior_color(page_content)
        record.transmissionType = self._parse_transmission_type(page_content)

        return record.dict()
