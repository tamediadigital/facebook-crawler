from typing import List

from crawlers.automotive_crawlers.cars_availability_check_crawler import CarsAvailabilityCheckCrawler
from crawlers.automotive_crawlers.delta_cars_crawler import DeltaCarsCrawler
from crawlers.automotive_crawlers.scroll_cars_crawler import ScrollCarsCrawler
from data_processor import DataProcessor
from utils.proxy import Proxy
from config import SOCIAL_PROXY_SERVER, SOCIAL_PROXY_USERNAME, SOCIAL_PROXY_PASS, SOCIAL_PROXY_KEY, \
    SOCIAL_PROXY_SECRET, SOCIAL_PROXY_B64_STR


if __name__ == '__main__':
    proxy: Proxy = Proxy(SOCIAL_PROXY_SERVER, SOCIAL_PROXY_USERNAME, SOCIAL_PROXY_PASS, SOCIAL_PROXY_KEY,
                         SOCIAL_PROXY_SECRET, SOCIAL_PROXY_B64_STR)
    # ScrollCarsCrawler(proxy).scrolling_process()

    # data_processor = DataProcessor()
    # data_processor.listings_to_check()
    # data_processor.delta_listings()
    # overlap_listings = data_processor.overlap_listings()

    delta_listings_with_details: List[dict] = DeltaCarsCrawler(proxy).get_details_for_delta_cars_process()
    # checked_listings: List[dict] = CarsAvailabilityCheckCrawler(proxy).cars_availability_check_process()
    # data_processor.make_snapshot(delta_listings_with_details, checked_listings, overlap_listings)
