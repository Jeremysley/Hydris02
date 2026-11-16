import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

from utils.db import init_db

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

COGS = [
    "cogs.moderation",
    "cogs.automod",
    "cogs.roles",
    "cogs.logging_cog",
]


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"Slash sync failed: {e}")


async def load_cogs():
    for ext in COGS:
        try:
            await bot.load_extension(ext)
            print(f"Loaded {ext}")
        except Exception as e:
            print(f"Failed to load {ext}: {e}")


async def main():
    if not TOKEN:
        raise RuntimeError("DISCORD_TOKEN not found. Did you create a .env file?")
    init_db()
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
