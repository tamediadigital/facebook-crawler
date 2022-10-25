import json
import requests

from config import CATEGORY_TO_PROCESS, ALERTINA_APP_ID, ALERTINA_URL


def slack_message_via_alertina(snapshot_len: int):
    data = {
        "appId": ALERTINA_APP_ID,
        "type": 'info',
        "message": f'*FACEBOOK* {CATEGORY_TO_PROCESS}: \n>{snapshot_len}'
        }
    requests.post(ALERTINA_URL, headers={'Content-Type': 'application/json'}, data=json.dumps(data))
