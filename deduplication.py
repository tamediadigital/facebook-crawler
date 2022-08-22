import os
import json
import gzip

from iteration_utilities import unique_everseen
from config import DATE
from logger import stdout_log
from s3_conn import s3_conn

YEAR, MONTH, DAY = DATE.split('-')
AGGREGATED_CITIES_FILE = f'facebook-aggregated-{YEAR}-{MONTH}-{DAY}.jsonl.gz'


def data_analysis():
    with gzip.open(AGGREGATED_CITIES_FILE) as f:
        all_listings = [json.loads(line) for line in f]

    stdout_log.info(f"Aggregated cities listings len: {len(all_listings)}")

    unique_ids = list(set([record["item_id"] for record in all_listings]))
    unique_listings = list(unique_everseen(all_listings))

    stdout_log.info(f"Unique aggregated ids of listings for cities len: {len(unique_ids)}")
    stdout_log.info(f"Unique aggregated listings for cities len: {len(unique_listings)}")

    unique_cities = list(set([record["item_city"] for record in unique_listings]))
    unique_cantons = list(set([record["item_canton_code"] for record in unique_listings]))

    stdout_log.info(f"Unique cities in listings len: {len(unique_cities)}, {unique_cities}")
    stdout_log.info(f"Unique cantons in listings len: {len(unique_cantons)}, {unique_cantons}")

    unique_aggregated_file: str = f"unique-{AGGREGATED_CITIES_FILE}"
    with gzip.open(unique_aggregated_file, "wb") as writer:
        for line in unique_listings:
            writer.write(line)
    writer.close()
    s3_conn.upload_file(f"unique-{AGGREGATED_CITIES_FILE}", per_city=False)

    # Per city
    result_per_city = {}
    for city in unique_cities:
        result_per_city[city] = {}
        city_result = [listing for listing in unique_listings if listing["item_city"] == city]
        result_per_city[city] = len(city_result)

    with open(f"unique-facebook-aggregated-results-per-city-{YEAR}-{MONTH}-{DAY}.json", "w") as f:
        json.dump(result_per_city, f)
    s3_conn.upload_file(f"unique-facebook-aggregated-results-per-city-{YEAR}-{MONTH}-{DAY}.json", per_city=False)

    # Per canton
    result_per_canton = {}
    for canton in unique_cantons:
        result_per_canton[canton] = {}
        canton_result = [listing for listing in unique_listings if listing["item_canton_code"] == canton]
        result_per_canton[canton] = len(canton_result)

    with open(f"unique-facebook-aggregated-results-per-canton-{YEAR}-{MONTH}-{DAY}.json", "w") as f:
        json.dump(result_per_canton, f)
    s3_conn.upload_file(f"unique-facebook-aggregated-results-per-canton-{YEAR}-{MONTH}-{DAY}.json", per_city=False)


def aggregate_per_city_files():
    with gzip.open(AGGREGATED_CITIES_FILE, "wb") as writer:
        for city in ['zurich', 'bern', 'lausanne', 'lugano', 'geneva', 'st_gallen', 'basel', 'luzern']:
            file_name = f"test-facebook-{city}-{YEAR}-{MONTH}-{DAY}.jsonl.gz"
            s3_conn.download_file(f'fb/year={YEAR}/month={MONTH}/day={DAY}/per-city/{file_name}', file_name)
            if file_name.endswith(".gz"):
                input = gzip.GzipFile(file_name, "rb")
                for line in input.readlines():
                    writer.write(line)
            os.remove(file_name)

    writer.close()
    s3_conn.upload_file(AGGREGATED_CITIES_FILE, per_city=False)


if __name__ == '__main__':
    aggregate_per_city_files()
    data_analysis()
