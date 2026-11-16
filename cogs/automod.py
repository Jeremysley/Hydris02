import re
import time
import discord
from discord.ext import commands
from discord import app_commands

from utils import db

INVITE_REGEX = re.compile(r"(discord\.gg|discordapp\.com/invite|discord\.com/invite)/\S+", re.IGNORECASE)

# very small starter banlist — expand as needed
BANNED_WORDS = {"badword1", "badword2"}

# user_id -> list of message timestamps (for spam detection)
message_log = {}
SPAM_LIMIT = 5       # messages
SPAM_WINDOW = 5       # seconds


class AutoMod(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        config = db.get_guild_config(message.guild.id)
        if config and config["automod_enabled"] == 0:
            return

        # --- invite link filter ---
        if INVITE_REGEX.search(message.content):
            await message.delete()
            await message.channel.send(
                f"{message.author.mention}, invite links aren't allowed here.",
                delete_after=5,
            )
            return

        # --- banned word filter ---
        lowered = message.content.lower()
        if any(word in lowered for word in BANNED_WORDS):
            await message.delete()
            await message.channel.send(
                f"{message.author.mention}, that language isn't allowed here.",
                delete_after=5,
            )
            return

        # --- spam filter ---
        now = time.time()
        key = (message.guild.id, message.author.id)
        timestamps = message_log.get(key, [])
        timestamps = [t for t in timestamps if now - t < SPAM_WINDOW]
        timestamps.append(now)
        message_log[key] = timestamps

        if len(timestamps) > SPAM_LIMIT:
            try:
                await message.author.timeout(
                    discord.utils.utcnow() + __import__("datetime").timedelta(minutes=1),
                    reason="Auto-mod: spam detected",
                )
                await message.channel.send(
                    f"{message.author.mention} was timed out for spamming.", delete_after=5
                )
            except discord.Forbidden:
                pass
            message_log[key] = []

    @app_commands.command(name="automod", description="Enable or disable auto-mod for this server")
    @app_commands.checks.has_permissions(administrator=True)
    async def automod_toggle(self, interaction: discord.Interaction, enabled: bool):
        db.set_guild_config(interaction.guild.id, automod_enabled=1 if enabled else 0)
        await interaction.response.send_message(
            f"Auto-mod is now {'enabled' if enabled else 'disabled'}."
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(AutoMod(bot))
