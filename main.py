from typing import List


from data_processing import DataProcessor
from config import CATEGORY_TO_PROCESS, DATE
from utils import stdout_log, prepare_proxies
from parsers import ScrollParser, AutomotiveParser, PropertyParser
from crawlers import ScrollCrawler, DetailsCrawler, AvailabilityCrawler


if __name__ == '__main__':
    stdout_log.info(f"DATE: {DATE}")
    # Prepare proxies
    proxies = prepare_proxies()

    # Scroll step
    scroll_parser = ScrollParser()
    ScrollCrawler(proxies, scroll_parser, CATEGORY_TO_PROCESS).scrolling_process()

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

    details_crawler = DetailsCrawler(proxies, delta_listings_parser, CATEGORY_TO_PROCESS)
    delta_listings: List[dict] = details_crawler.pagination_process()

    # Check listing availability step.
    if CATEGORY_TO_PROCESS != "vehicle":
        availability_crawler = AvailabilityCrawler(proxies, CATEGORY_TO_PROCESS)
        available_listings: List[dict] = availability_crawler.availability_check_process()
    else:
        available_listings = data_processor.listings_to_check()

    # Make snapshot step.
    data_processor.make_snapshot(delta_listings, available_listings, overlap_listings, listing_not_to_check)
