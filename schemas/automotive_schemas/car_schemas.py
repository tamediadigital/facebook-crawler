from typing import Optional, List
from schemas.automotive_schemas.base_automotive_schemas import BaseItem, Seller


class PartialCar(BaseItem):
    short_desc: Optional[str]
    mileage: Optional[str]


class Car(PartialCar):
    title: str
    publish_time: str
    description: Optional[str]
    seller: Optional[Seller]
    images: Optional[List[str]]
