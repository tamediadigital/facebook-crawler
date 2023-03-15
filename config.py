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
MAX_PAGE_HEIGHT = int(os.environ.get("MAX_PAGE_HEIGHT")) if os.environ.get("MAX_PAGE_HEIGHT") else 70000

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

ALERTINA_APP_ID = os.environ.get("ALERTINA_APP_ID")
ALERTINA_URL = os.environ.get("ALERTINA_URL")

S3_BUCKET = os.environ.get("BUCKET_NAME")
S3_PREFIX = os.environ.get("S3_PREFIX")

REDIS_HOST: str = os.environ.get("REDIS_HOST")
REDIS_PORT: int = int(os.environ.get("REDIS_PORT"))
REDIS_DB: int = int(os.environ.get("REDIS_DB"))

# PROXIES SETUP
PROXIES_LIST: list = os.environ.get("PROXIES_LIST").split('-') if os.environ.get("PROXIES_LIST") else ["AU"]
PROXY_CREDS_MAP = {
    "SOCIAL_PROXY_KEY": os.environ.get("SOCIAL_PROXY_KEY"),
    "SOCIAL_PROXY_SECRET": os.environ.get("SOCIAL_PROXY_SECRET"),
    "SOCIAL_PROXY_USERNAME_AU": os.environ.get("SOCIAL_PROXY_USERNAME"),
    "SOCIAL_PROXY_PASS_AU": os.environ.get("SOCIAL_PROXY_PASS"),
    "SOCIAL_PROXY_SERVER_AU": os.environ.get("SOCIAL_PROXY_SERVER"),
    "SOCIAL_PROXY_B64_STR_AU": os.environ.get("SOCIAL_PROXY_B64_STR"),
    "SOCIAL_PROXY_USERNAME_UK": os.environ.get("SOCIAL_PROXY_USERNAME_UK"),
    "SOCIAL_PROXY_PASS_UK": os.environ.get("SOCIAL_PROXY_PASS_UK"),
    "SOCIAL_PROXY_SERVER_UK": "london1.thesocialproxy.com:10000",
    "SOCIAL_PROXY_B64_STR_UK": os.environ.get("SOCIAL_PROXY_B64_STR_UK"),
    }

DATE: str = os.environ.get("DATE")
if not DATE:
    DATE = datetime.now().date().strftime("%Y-%m-%d")

PAGE_HEIGHT_SCROLL_POOL: List[int] = [15000, 15500, 16000, 16500, 17000, 17500, 18000, 18500, 19000, 19500, 20000,
                                      20500]
PAGE_TIMEOUT_SCROLL_POOL: List[int] = [4, 4.5, 5, 5.5, 6.5, 7, 7.5]
PAGE_TIMEOUT_PAGINATING_POOL: List[int] = [0.5, 0.6, 0.7, 0.8, 0.9, 1, 1.1, 1.2, 1.3, 1.4, 1.5]

LISTINGS_NUM_PER_PROXY = int(os.environ.get("LISTINGS_NUM_PER_PROXY")) \
    if os.environ.get("LISTINGS_NUM_PER_PROXY") else 50

LISTINGS_TO_CHECK_SIZE = int(os.environ.get("LISTINGS_TO_CHECK_SIZE")) \
    if os.environ.get("LISTINGS_TO_CHECK_SIZE") else 8000

MAX_DAYS_OF_MISSING_SNAPSHOT_FROM_PREVIOUS_DAY = int(os.environ.get("MAX_DAYS_OF_MISSING_SNAPSHOT_FROM_PREVIOUS_DAY")) \
    if os.environ.get("MAX_DAYS_OF_MISSING_SNAPSHOT_FROM_PREVIOUS_DAY") else 5
