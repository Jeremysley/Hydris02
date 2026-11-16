import discord
from discord.ext import commands
from discord import app_commands

from utils import db


class Roles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="reactionrole", description="Set up a reaction role on a message")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def reactionrole(
        self,
        interaction: discord.Interaction,
        message_id: str,
        emoji: str,
        role: discord.Role,
    ):
        try:
            msg_id = int(message_id)
        except ValueError:
            await interaction.response.send_message("That message ID doesn't look valid.", ephemeral=True)
            return

        message = None
        for channel in interaction.guild.text_channels:
            try:
                message = await channel.fetch_message(msg_id)
                break
            except (discord.NotFound, discord.Forbidden):
                continue

        if not message:
            await interaction.response.send_message(
                "Couldn't find that message. Make sure the ID is correct and I can see the channel.",
                ephemeral=True,
            )
            return

        await message.add_reaction(emoji)
        db.add_reaction_role(msg_id, emoji, role.id, interaction.guild.id)
        await interaction.response.send_message(
            f"Reacting with {emoji} on that message now gives the {role.mention} role."
        )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.member is None or payload.member.bot:
            return

        entry = db.get_reaction_role(payload.message_id, str(payload.emoji))
        if not entry:
            return

        guild = self.bot.get_guild(payload.guild_id)
        role = guild.get_role(entry["role_id"])
        if role:
            await payload.member.add_roles(role, reason="Reaction role")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        entry = db.get_reaction_role(payload.message_id, str(payload.emoji))
        if not entry:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        member = guild.get_member(payload.user_id)
        role = guild.get_role(entry["role_id"])
        if member and role:
            await member.remove_roles(role, reason="Reaction role removed")


async def setup(bot: commands.Bot):
    await bot.add_cog(Roles(bot))
