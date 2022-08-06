#!python3.9
import os, sys
import json

import requests

if not __debug__:
    from dotenv import load_dotenv
    load_dotenv('../.env')

BOT_TOKEN = os.getenv('DISCORD_TOKEN')
APPLICATION_ID = os.getenv('APPLICATION_ID')
APPLICATION_PUBLIC_KEY = os.getenv('APPLICATION_PUBLIC_KEY')

url = f"https://discord.com/api/v9/applications/{APPLICATION_ID}/commands"
headers = {
    "Authorization": f"Bot {BOT_TOKEN}"
}

def get() -> None:
    payload = {
        "with_localizations" : True
    }
    r = requests.get(url, headers=headers, params=payload)
    print(r.status_code)
    print(json.dumps(r.json(), ensure_ascii=False, indent=4))

if __name__ == '__main__':
    get()

