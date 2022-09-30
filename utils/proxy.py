import json
import requests


from utils.logger import stdout_log


class Proxy:
    def __init__(self, server: str, username: str, password: str, key: str = None, secret: str = None,
                 bs4_str: str = None):
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

        proxy_list: list = json.loads(requests.request("GET", url, headers=headers, data=payload).text)
        stdout_log.info(proxy_list)
