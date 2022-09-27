import os
from datetime import datetime

DEFAULT_REQUIRED_CITIES = ["zurich", "bern", "lausanne", "lugano", "geneva", "st_gallen", "basel", "luzern"]
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
    'luzern': '115581378455439'
    }

DEFAULT_PRICE_COMBINATIONS: list = ["?maxPrice=1500&minPrice=200", "?maxPrice=5500&minPrice=1500",
                                    "?maxPrice=11500&minPrice=5500", "?maxPrice=22500&minPrice=11500",
                                    "?maxPrice=1150000&minPrice=22500"]
PRICE_COMBINATIONS: list = os.environ.get("PRICE_COMBINATIONS").split("-") \
    if os.environ.get("PRICE_COMBINATIONS") else DEFAULT_REQUIRED_CITIES

FB_BOT_CREDENTIALS_PAIR = os.environ.get("FB_BOT_CREDENTIALS_PAIR")

REQUIRED_RANGES_IN_KM: list = os.environ.get("REQUIRED_RANGES_IN_KM").split("-") \
    if os.environ.get("REQUIRED_RANGES_IN_KM") else []
REQUIRED_CITIES: list = os.environ.get("REQUIRED_CITIES").split("-") if os.environ.get("REQUIRED_CITIES") \
    else DEFAULT_REQUIRED_CITIES

FB_BOT_EMAIL: str = os.environ.get(f"FB_BOT_EMAIL_{FB_BOT_CREDENTIALS_PAIR}")
FB_BOT_PASS: str = os.environ.get(f"FB_BOT_PASS_{FB_BOT_CREDENTIALS_PAIR}")

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
