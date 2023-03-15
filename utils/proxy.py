import json
import requests

from typing import List
from utils.logger import stdout_log
from config import PROXY_CREDS_MAP, PROXIES_LIST


class Proxy:
    def __init__(self, server: str, username: str, password: str, key: str = None, secret: str = None, bs4_str: str = None):
        self.server = server
        self.username = username
        self.password = password
        self.key = key
        self.secret = secret
        self.bs4_str = bs4_str

    def rotate_proxy_call(self):
        stdout_log.info(f"Rotate proxy call triggered.")
        url: str = f"https://thesocialproxy.com/wp-json/lmfwc/v2/licenses/rotate-proxy/{self.bs4_str}" \
                   f"/?consumer_key={self.key}&consumer_secret={self.secret}"

        payload = {}
        headers = {
            'Content-Type': 'application/json'
            }

        # TODO: Handle this better.
        try:
            response = requests.request("GET", url, headers=headers, data=payload).text
            proxy_list: list = json.loads(response)
            stdout_log.info(proxy_list)
        except:
            stdout_log.info(f"Proxy endpoint bad response.")


def prepare_proxies() -> List[Proxy]:
    proxies = []
    for proxy_region in PROXIES_LIST:
        proxies.append(Proxy(server=PROXY_CREDS_MAP[f"SOCIAL_PROXY_SERVER_{proxy_region}"],
                             username=PROXY_CREDS_MAP[f"SOCIAL_PROXY_USERNAME_{proxy_region}"],
                             password=PROXY_CREDS_MAP[f"SOCIAL_PROXY_PASS_{proxy_region}"],
                             key=PROXY_CREDS_MAP["SOCIAL_PROXY_KEY"],
                             secret=PROXY_CREDS_MAP["SOCIAL_PROXY_SECRET"],
                             bs4_str=PROXY_CREDS_MAP[f"SOCIAL_PROXY_B64_STR_{proxy_region}"]))

    return proxies
