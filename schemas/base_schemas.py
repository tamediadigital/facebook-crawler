from pydantic import BaseModel
from typing import List
from datetime import datetime


class BaseRecord(BaseModel):
    adId: str = None
    crawlerSource: str = "CIC"
    source: str = "facebook_marketplace"
    language: str = "en"
    city: str = None
    cantonCode: str = None
    title: str = None
    url: str = None
    price: str = None
    description: str = None
    imageLinks: List[str] = None
    crawlDatetime: str = str(datetime.now())
    availableFrom: str = None
    isBoosted: str = None
    sellerId: str = None
    sellerName: str = None
    sellerType: str = None
    last_check: str = str(datetime.now())


class RecordFromScroll(BaseModel):
    adId: str
    url: str
    price: str
    city: str
    cantonCode: str
