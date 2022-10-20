import os
from datetime import datetime
from typing import List

DEFAULT_REQUIRED_CITIES = ["zurich", "bern", "lausanne", "lugano", "geneva", "st_gallen", "basel", "luzern", "chur",
                           "thun", "sion", "fribourg", "olten"]
CITIES_MAP = {
    'zurich': 'Zürich, Switzerland',
    'bern': 'Bern',
    'lausanne': 'Lausanne, Switzerland',
    'lugano': 'Lugano, Switzerland',
    'geneva': 'Geneva, Switzerland',
    'st_gallen': 'Saint Gallen',
    'basel': 'Basel, Switzerland',
    'luzern': 'Luzern, Switzerland'
    }

CITIES_CITIES_CODE_MAP = {
    'zurich': 'zurich',
    'bern': '108108499217446',
    'lausanne': '115456095134627',
    'lugano': '106534719384213',
    'geneva': '110868505604715',
    'st_gallen': '110759738952928',
    'basel': '108671032497097',
    'luzern': '115581378455439',
    'chur': '106239312747810',
    'thun': '114513118565117',
    'sion': '109513215741594',
    'fribourg': '108257202542190',
    'olten': '114243855254869'
    }

DEFAULT_PRICE_COMBINATIONS: list = ["?maxPrice=1500&minPrice=200", "?maxPrice=5500&minPrice=1500",
                                    "?maxPrice=11500&minPrice=5500", "?maxPrice=22500&minPrice=11500",
                                    "?maxPrice=1150000&minPrice=22500"]
PRICE_COMBINATIONS: list = os.environ.get("PRICE_COMBINATIONS").split("-") \
    if os.environ.get("PRICE_COMBINATIONS") else DEFAULT_PRICE_COMBINATIONS

FB_BOT_CREDENTIALS_PAIR = os.environ.get("FB_BOT_CREDENTIALS_PAIR")

REQUIRED_RANGES_IN_KM: list = os.environ.get("REQUIRED_RANGES_IN_KM").split("-") \
    if os.environ.get("REQUIRED_RANGES_IN_KM") else []
REQUIRED_CITIES: list = os.environ.get("REQUIRED_CITIES").split("-") if os.environ.get("REQUIRED_CITIES") \
    else DEFAULT_REQUIRED_CITIES

CATEGORY_TO_PROCESS = os.environ.get("CATEGORY_TO_PROCESS")
MAX_PAGE_HEIGHT = os.environ.get("MAX_PAGE_HEIGHT")

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

S3_BUCKET = os.environ.get("BUCKET_NAME")
S3_PREFIX = os.environ.get("S3_PREFIX")

REDIS_HOST: str = os.environ.get("REDIS_HOST")
REDIS_PORT: int = int(os.environ.get("REDIS_PORT"))
REDIS_DB: int = int(os.environ.get("REDIS_DB"))

SOCIAL_PROXY_USERNAME: str = os.environ.get("SOCIAL_PROXY_USERNAME")
SOCIAL_PROXY_PASS: str = os.environ.get("SOCIAL_PROXY_PASS")
SOCIAL_PROXY_SERVER: str = os.environ.get("SOCIAL_PROXY_SERVER")
SOCIAL_PROXY_KEY: str = os.environ.get("SOCIAL_PROXY_KEY")
SOCIAL_PROXY_SECRET: str = os.environ.get("SOCIAL_PROXY_SECRET")
SOCIAL_PROXY_B64_STR: str = os.environ.get("SOCIAL_PROXY_B64_STR")

DATE: str = os.environ.get("DATE")
if not DATE:
    DATE = datetime.now().date().strftime("%Y-%m-%d")

PAGE_HEIGHT_SCROLL_POOL: List[int] = [15000, 15500, 16000, 16500, 17000, 17500, 18000, 18500, 19000, 19500, 20000,
                                      20500]
PAGE_TIMEOUT_SCROLL_POOL: List[int] = [4, 4.5, 5, 5.5, 6.5, 7, 7.5]

LISTINGS_NUM_PER_PROXY = int(os.environ.get("LISTINGS_NUM_PER_PROXY")) \
    if os.environ.get("LISTINGS_NUM_PER_PROXY") else 20
