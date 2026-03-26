import discord
from discord.ext import commands
from discord import app_commands
import os

class Reload(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="reload", description="Reload a command (Admin only)")
    async def reload(self, interaction: discord.Interaction, cog: str):
        # Admin check
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You must be an admin to use this command.", ephemeral=True)
            return

        cog_path = f"cogs.{cog}"

        try:
            await self.bot.reload_extension(cog_path)
            await interaction.response.send_message(f"✅ Successfully reloaded `{cog}`.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to reload `{cog}`: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Reload(bot))