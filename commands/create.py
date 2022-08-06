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

url = f"https://discord.com/api/v10/applications/{APPLICATION_ID}/commands"
headers = {
    "Authorization": f"Bot {BOT_TOKEN}"
}

def create(payload: dict) -> None:
    r = requests.post(url, headers=headers, json=payload)
    print(r.status_code)
    print(json.dumps(r.json(), ensure_ascii=False, indent=4))

if __name__ == '__main__':
    try:
        fp = sys.argv[1]
    except IndexError:
        fp = input("command file path: ")

    with open(fp, "r", encoding="utf-8") as f:
        payload = json.load(f)
    
    create(payload)

