import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta

from utils import db


class ConfirmNuke(discord.ui.View):
    def __init__(self, author: discord.Member):
        super().__init__(timeout=15)
        self.author = author
        self.confirmed = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(
                "Only the person who ran this command can confirm.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Confirm Nuke", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = True
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = False
        await interaction.response.send_message("Cancelled.", ephemeral=True)
        self.stop()


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def log_action(self, guild: discord.Guild, embed: discord.Embed):
        config = db.get_guild_config(guild.id)
        if config and config["mod_log_channel"]:
            channel = guild.get_channel(config["mod_log_channel"])
            if channel:
                await channel.send(embed=embed)

    # ---------- KICK ----------
    @app_commands.command(name="kick", description="Kick a member from the server")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason given"):
        await member.kick(reason=reason)
        embed = discord.Embed(title="Member Kicked", color=discord.Color.orange())
        embed.add_field(name="User", value=f"{member} ({member.id})", inline=False)
        embed.add_field(name="Moderator", value=str(interaction.user), inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        await interaction.response.send_message(embed=embed)
        await self.log_action(interaction.guild, embed)

    # ---------- BAN ----------
    @app_commands.command(name="ban", description="Ban a member from the server")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason given"):
        await member.ban(reason=reason)
        embed = discord.Embed(title="Member Banned", color=discord.Color.red())
        embed.add_field(name="User", value=f"{member} ({member.id})", inline=False)
        embed.add_field(name="Moderator", value=str(interaction.user), inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        await interaction.response.send_message(embed=embed)
        await self.log_action(interaction.guild, embed)

    # ---------- TIMEOUT ----------
    @app_commands.command(name="timeout", description="Timeout a member for N minutes")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "No reason given"):
        duration = timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        embed = discord.Embed(title="Member Timed Out", color=discord.Color.gold())
        embed.add_field(name="User", value=f"{member} ({member.id})", inline=False)
        embed.add_field(name="Duration", value=f"{minutes} minute(s)", inline=False)
        embed.add_field(name="Moderator", value=str(interaction.user), inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        await interaction.response.send_message(embed=embed)
        await self.log_action(interaction.guild, embed)

    # ---------- WARN ----------
    @app_commands.command(name="warn", description="Warn a member")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason given"):
        db.add_warn(interaction.guild.id, member.id, interaction.user.id, reason)
        embed = discord.Embed(title="Member Warned", color=discord.Color.yellow())
        embed.add_field(name="User", value=f"{member} ({member.id})", inline=False)
        embed.add_field(name="Moderator", value=str(interaction.user), inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        await interaction.response.send_message(embed=embed)
        await self.log_action(interaction.guild, embed)

    # ---------- WARNINGS ----------
    @app_commands.command(name="warnings", description="View a member's warnings")
    async def warnings(self, interaction: discord.Interaction, member: discord.Member):
        warns = db.get_warns(interaction.guild.id, member.id)
        if not warns:
            await interaction.response.send_message(f"{member.mention} has no warnings.")
            return
        embed = discord.Embed(title=f"Warnings for {member}", color=discord.Color.blue())
        for w in warns[:10]:
            embed.add_field(
                name=f"#{w['id']} — {w['timestamp']}",
                value=f"Reason: {w['reason']}\nBy: <@{w['moderator_id']}>",
                inline=False,
            )
        await interaction.response.send_message(embed=embed)

    # ---------- CLEAR WARNINGS ----------
    @app_commands.command(name="clearwarns", description="Clear all warnings for a member")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def clearwarns(self, interaction: discord.Interaction, member: discord.Member):
        db.clear_warns(interaction.guild.id, member.id)
        await interaction.response.send_message(f"Cleared all warnings for {member.mention}.")

    # ---------- NUKE ----------
    @app_commands.command(name="nuke", description="Clear all channels, rename it, and strip all member roles")
    async def nuke(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        channel = channel or interaction.channel

        view = ConfirmNuke(author=interaction.user)
        await interaction.response.send_message(
            f"⚠️ This will permanently delete all messages in {channel.mention}, rename it to "
            f"**nuked**, and remove every role from every member in the server. Confirm?",
            view=view,
            ephemeral=True,
        )
        await view.wait()

        if not view.confirmed:
            return

        # --- recreate the channel to wipe message history, and rename it ---
        position = channel.position
        new_channel = await channel.clone(name="nuked", reason=f"Nuked by {interaction.user}")
        await channel.delete()
        await new_channel.edit(position=position)

        # --- strip all roles from every member (roles themselves are not deleted) ---
        removable_roles = [
            role for role in interaction.guild.roles
            if role.name != "@everyone" and not role.managed and role < interaction.guild.me.top_role
        ]
        stripped_count = 0
        for member in interaction.guild.members:
            member_roles = [r for r in member.roles if r in removable_roles]
            if member_roles:
                try:
                    await member.remove_roles(*member_roles, reason=f"Server nuked by {interaction.user}")
                    stripped_count += 1
                except discord.Forbidden:
                    pass

        embed = discord.Embed(
            title="💥 Server Nuked",
            description=(
                f"Channel cleared and renamed by {interaction.user.mention}.\n"
                f"Roles stripped from **{stripped_count}** member(s)."
            ),
            color=discord.Color.red(),
        )
        await new_channel.send(embed=embed)

    # ---------- SET MOD LOG CHANNEL ----------
    @app_commands.command(name="setmodlog", description="Set the channel for moderation logs")
    @app_commands.checks.has_permissions(administrator=True)
    async def setmodlog(self, interaction: discord.Interaction, channel: discord.TextChannel):
        db.set_guild_config(interaction.guild.id, mod_log_channel=channel.id)
        await interaction.response.send_message(f"Mod log channel set to {channel.mention}.")

    # ---------- ERROR HANDLER ----------
    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "You don't have permission to use this command.", ephemeral=True
            )
        else:
            await interaction.response.send_message(f"Error: {error}", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
