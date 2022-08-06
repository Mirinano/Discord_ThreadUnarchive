#!python3.9
import os
from bot import Bot

if not __debug__:
    from dotenv import load_dotenv
    load_dotenv('.env')

BOT_TOKEN = os.getenv('DISCORD_TOKEN')

bot = Bot()

bot.run(BOT_TOKEN)