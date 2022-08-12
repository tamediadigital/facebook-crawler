from crawlers import FacebookCarCrawler
from config import REQUIRED_CITY, FB_BOT_EMAIL, FB_BOT_PASS, STRICT_SCROLL
from logger import stdout_log


def main():
    stdout_log.info(f"REQUIRED_CITY {REQUIRED_CITY}")
    stdout_log.info(f"FB_BOT_EMAIL {FB_BOT_EMAIL}")
    crawler = FacebookCarCrawler(required_cities=REQUIRED_CITY, fb_bot_email=FB_BOT_EMAIL, fb_bot_pass=FB_BOT_PASS,
                                 strict_scroll=STRICT_SCROLL)
    stdout_log.info("FacebookCarCrawler init.")
    stdout_log.info(f"STRICT_SCROLL {STRICT_SCROLL}")

    crawler.crawling_process()


if __name__ == '__main__':
    main()
