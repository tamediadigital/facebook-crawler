from dataclasses import dataclass


@dataclass
class CategoriesToProcess:
    CARS: str = "cars"
    VEHICLE: str = "vehicle"
    PROPERTY_FOR_SALE: str = "propertyrentals"
    PROPERTY_FOR_RENT: str = "propertyforsale"


@dataclass
class Listings:
    TO_CHECK: str = "listings-to-check"
    DELTA: str = "delta-listings"
    OVERLAP: str = "overlap-listings"
    SNAPSHOT: str = "snapshot-fb"
    AVAILABLE: str = "available-listings"
    PAGINATED_DELTA: str = "paginated-delta-listings"


CATEGORIES = CategoriesToProcess()
LISTINGS = Listings()
