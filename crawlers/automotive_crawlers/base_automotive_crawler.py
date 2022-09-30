from config import PAGE_HEIGHT_SCROLL_POOL, PAGE_TIMEOUT_SCROLL_POOL, LISTINGS_NUM_PER_PROXY
from crawlers.base_crawler import BaseCrawler
from db.redis_db import redis_client
from utils.proxy import Proxy


class BaseCarsCrawler(BaseCrawler):
    def __init__(self, proxy: Proxy):
        super().__init__()
        self.proxy = proxy
        self.redis_client = redis_client
        self.page_height_scroll_pool = PAGE_HEIGHT_SCROLL_POOL
        self.page_timeout_scroll_pool = PAGE_TIMEOUT_SCROLL_POOL
        self.listings_num_per_proxy = LISTINGS_NUM_PER_PROXY
