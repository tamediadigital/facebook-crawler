import os
from datetime import datetime

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

FB_BOT_CREDENTIALS_PAIR = os.environ.get("FB_BOT_CREDENTIALS_PAIR")
CRAWL_TYPE = os.environ.get("CRAWL_TYPE")

REQUIRED_RANGES_IN_KM: list = os.environ.get("REQUIRED_RANGES_IN_KM").split("-") if os.environ.get("REQUIRED_RANGES_IN_KM") else []
REQUIRED_CITY: list = os.environ.get("REQUIRED_CITY").split("-") if os.environ.get("REQUIRED_CITY") else []
SCROLL_HEIGHT: int = int(os.environ.get("SCROLL_HEIGHT")) if os.environ.get("SCROLL_HEIGHT") else 3000

FB_BOT_EMAIL: str = os.environ.get(f"FB_BOT_EMAIL_{FB_BOT_CREDENTIALS_PAIR}")
FB_BOT_PASS: str = os.environ.get(f"FB_BOT_PASS_{FB_BOT_CREDENTIALS_PAIR}")

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

S3_BUCKET = os.environ.get("BUCKET_NAME")
S3_PREFIX = os.environ.get("S3_PREFIX")

REDIS_HOST: str = os.environ.get("REDIS_HOST")
REDIS_PORT: int = int(os.environ.get("REDIS_PORT"))
REDIS_DB: int = int(os.environ.get("REDIS_DB"))

DATE: str = os.environ.get("DATE")
if not DATE:
    DATE = datetime.now().date().strftime("%Y-%m-%d")
