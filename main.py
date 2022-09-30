from typing import List

from crawlers.automotive_crawlers.cars_availability_check_crawler import CarsAvailabilityCheckCrawler
from crawlers.automotive_crawlers.delta_cars_crawler import DeltaCarsCrawler
from crawlers.automotive_crawlers.scroll_cars_crawler import ScrollCarsCrawler
from data_processor import DataProcessor


if __name__ == '__main__':
    ScrollCarsCrawler().scrolling_process()

    data_processor = DataProcessor()
    data_processor.listings_to_check()
    data_processor.delta_listings()
    overlap_listings = data_processor.overlap_listings()

    delta_listings_with_details: List[dict] = DeltaCarsCrawler().get_details_for_delta_cars_process()
    checked_listings: List[dict] = CarsAvailabilityCheckCrawler().cars_availability_check_process()
    data_processor.make_snapshot(delta_listings_with_details, checked_listings, overlap_listings)
