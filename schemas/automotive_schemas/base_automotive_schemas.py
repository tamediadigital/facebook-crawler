from pydantic import BaseModel


class Seller(BaseModel):
    seller_id: str
    seller_name: str


class BaseItem(BaseModel):
    ad_id: str
    url: str
    price: str
    city: str
    canton_code: str
