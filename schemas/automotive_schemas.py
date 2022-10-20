from schemas.base_schemas import BaseRecord


class AutomotiveRecord(BaseRecord):
    type: str = "automotive"
    vehicleType: str = "vehicle"
    condition: str = None
    conditionType: str = None
    originalCategoryId: str = "807311116002614"
    mileage: str = None
    make: str = None
    model: str = None
    hp: str = None
    fuelType: str = None
    bodyColor: str = None
    interiorColor: str = None
    transmissionType: str = None
