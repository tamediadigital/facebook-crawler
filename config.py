import os

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

# CRAWLER_NAME = os.environ.get("CRAWLER_NAME")
FB_BOT_CREDENTIALS_PAIR = os.environ.get("FB_BOT_CREDENTIALS_PAIR")
CRAWL_TYPE = os.environ.get("CRAWL_TYPE")
DATETIME = os.environ.get("DATETIME")

# REQUIRED_RANGES_IN_KM = os.environ.get("REQUIRED_RANGES_IN_KM")
REQUIRED_RANGES_IN_KM = [1, 2, 5, 10, 20, 40, 60]
REQUIRED_CITY = os.environ.get("REQUIRED_CITY").split("-")
STRICT_SCROLL: str = os.environ.get("STRICT_SCROLL")

FB_BOT_EMAIL: str = os.environ.get(f"FB_BOT_EMAIL_{FB_BOT_CREDENTIALS_PAIR}")
FB_BOT_PASS: str = os.environ.get(f"FB_BOT_PASS_{FB_BOT_CREDENTIALS_PAIR}")

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

S3_BUCKET = os.environ.get("BUCKET_NAME")
S3_PREFIX = os.environ.get("S3_PREFIX")
