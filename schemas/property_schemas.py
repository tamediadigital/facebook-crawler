from schemas.base_schemas import BaseRecord


class PropertyRecord(BaseRecord):
    type: str = "property"
    address: str = None
    propertyType: str = None
    livingSpace: str = None
    rooms: str = None
    bathrooms: str = None
    parking: str = None


class PropertyForRent(PropertyRecord):
    saleType: str = "rent"
    originalCategoryId: str = "807311116002614"


class PropertyForSale(PropertyRecord):
    saleType: str = "sale"
    originalCategoryId: str = "821056594720130"
