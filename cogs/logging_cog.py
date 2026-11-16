import discord
from discord.ext import commands

from utils import db


class LoggingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def get_log_channel(self, guild: discord.Guild):
        config = db.get_guild_config(guild.id)
        if config and config["mod_log_channel"]:
            return guild.get_channel(config["mod_log_channel"])
        return None

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        channel = await self.get_log_channel(message.guild)
        if not channel:
            return
        embed = discord.Embed(title="Message Deleted", color=discord.Color.dark_red())
        embed.add_field(name="Author", value=str(message.author), inline=False)
        embed.add_field(name="Channel", value=message.channel.mention, inline=False)
        embed.add_field(name="Content", value=message.content or "*(no text content)*", inline=False)
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot or not before.guild or before.content == after.content:
            return
        channel = await self.get_log_channel(before.guild)
        if not channel:
            return
        embed = discord.Embed(title="Message Edited", color=discord.Color.orange())
        embed.add_field(name="Author", value=str(before.author), inline=False)
        embed.add_field(name="Channel", value=before.channel.mention, inline=False)
        embed.add_field(name="Before", value=before.content or "*(empty)*", inline=False)
        embed.add_field(name="After", value=after.content or "*(empty)*", inline=False)
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel = await self.get_log_channel(member.guild)
        if not channel:
            return
        embed = discord.Embed(title="Member Joined", color=discord.Color.green())
        embed.add_field(name="User", value=f"{member} ({member.id})")
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        channel = await self.get_log_channel(member.guild)
        if not channel:
            return
        embed = discord.Embed(title="Member Left", color=discord.Color.dark_grey())
        embed.add_field(name="User", value=f"{member} ({member.id})")
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(LoggingCog(bot))
