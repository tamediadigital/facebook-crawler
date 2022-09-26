from typing import List, Optional
from pydantic import BaseModel


class BaseItem(BaseModel):
    ad_id: str
    url: str
    price: str
    city: str
    canton_code: str
    short_desc: Optional[str]
    mileage: Optional[str]
