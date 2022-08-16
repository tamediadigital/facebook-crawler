import json
import redis
import backoff

from config import REDIS_PORT, REDIS_HOST, REDIS_DB


class Redis:
    def __init__(self):
        self.client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    def insert_into_redis(self, json_value):
        self.client.set('facebook-unscrolled-required-cities', json.dumps(json_value))

    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    def get_mappings(self):
        return json.loads(self.client.get('facebook-unscrolled-required-cities').decode('utf8'))


redis_client = Redis()
