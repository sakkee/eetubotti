from src.bot import Bot
from dotenv import load_dotenv
import os
import discord

load_dotenv()
token = os.getenv("TOKEN")

if __name__ == '__main__':
    discord_bot = Bot(token=token)

    discord_bot.start()
