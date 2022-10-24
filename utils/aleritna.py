import json
import requests

from config import CATEGORY_TO_PROCESS, ALERTINA_APP_ID, ALERTINA_URL


def slack_message_via_alertina(collected_items: int):
    data = {
        "appId": ALERTINA_APP_ID,
        "type": 'info',
        "message": f'*FACEBOOK* {CATEGORY_TO_PROCESS}: \n>{collected_items}'
        }
    requests.post(ALERTINA_URL, headers={'Content-Type': 'application/json'}, data=json.dumps(data))
