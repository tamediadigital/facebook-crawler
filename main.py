from typing import List

from crawlers import ScrollCrawler, DetailsCrawler, AvailabilityCrawler
from data_processing import DataProcessor
from parsers import ScrollParser, AutomotiveParser, PropertyParser
from utils import Proxy
from config import SOCIAL_PROXY_SERVER, SOCIAL_PROXY_USERNAME, SOCIAL_PROXY_PASS, SOCIAL_PROXY_KEY, \
    SOCIAL_PROXY_SECRET, SOCIAL_PROXY_B64_STR, CATEGORY_TO_PROCESS


if __name__ == '__main__':
    proxy: Proxy = Proxy(SOCIAL_PROXY_SERVER, SOCIAL_PROXY_USERNAME, SOCIAL_PROXY_PASS, SOCIAL_PROXY_KEY,
                         SOCIAL_PROXY_SECRET, SOCIAL_PROXY_B64_STR)

    # Scroll step
    scroll_parser = ScrollParser()
    ScrollCrawler(proxy, scroll_parser, CATEGORY_TO_PROCESS).scrolling_process()

    # Data processing step
    data_processor = DataProcessor(CATEGORY_TO_PROCESS)
    listing_not_to_check = data_processor.listings_to_check()
    data_processor.delta_listings()
    overlap_listings = data_processor.overlap_listings()

    # Paginate delta listings step.
    if CATEGORY_TO_PROCESS in ["vehicle", "cars"]:
        delta_listings_parser = AutomotiveParser()
    else:
        delta_listings_parser = PropertyParser()

    details_crawler = DetailsCrawler(proxy, delta_listings_parser, CATEGORY_TO_PROCESS)
    delta_listings: List[dict] = details_crawler.pagination_process()

    # Check listing availability step.
    if CATEGORY_TO_PROCESS != "vehicle":
        availability_crawler = AvailabilityCrawler(proxy, CATEGORY_TO_PROCESS)
        available_listings: List[dict] = availability_crawler.availability_check_process()
    else:
        available_listings = data_processor.listings_to_check()

    # Make snapshot step.
    data_processor.make_snapshot(delta_listings, available_listings, overlap_listings, listing_not_to_check)
