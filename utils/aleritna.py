import json
import requests

from config import CATEGORY_TO_PROCESS, ALERTINA_APP_ID, ALERTINA_URL


def slack_message_via_alertina(snapshot_len: int, delta_len: int, listing_to_check_len: int, overlap_len: int,
                               listing_not_to_check: int):
    data = {
        "appId": ALERTINA_APP_ID,
        "type": 'info',
        "message": f'*FACEBOOK* {CATEGORY_TO_PROCESS}: \n>{snapshot_len} \n> found-in-scroll: {delta_len+overlap_len}'
                   f'\n> delta-listings: {delta_len} \n> overlap-listings: {overlap_len} \n>'
                   f'listing-to-check: {listing_to_check_len} \n> not-checked-listings: {listing_not_to_check}'
        }
    requests.post(ALERTINA_URL, headers={'Content-Type': 'application/json'}, data=json.dumps(data))


def slack_alert_when_proxy_is_blocked(proxy_server):
    data = {
        "appId": ALERTINA_APP_ID,
        "type": 'bad',
        "message": f'*FACEBOOK* {CATEGORY_TO_PROCESS}: Proxy: {proxy_server} is blocked!'
        }
    requests.post(ALERTINA_URL, headers={'Content-Type': 'application/json'}, data=json.dumps(data))
