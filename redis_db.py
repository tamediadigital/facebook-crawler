import json
import redis
import backoff

from config import REDIS_PORT, REDIS_HOST, REDIS_DB


class Redis:
    def __init__(self):
        self.client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

    # TODO: Improve key
    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    def insert_into_redis(self, json_value, key='facebook-unscrolled-required-cities'):
        self.client.set(key, json.dumps(json_value))

    # TODO: Improve key
    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    def get_mappings(self, key='facebook-unscrolled-required-cities'):
        return json.loads(self.client.get(key).decode('utf8'))


redis_client = Redis()
