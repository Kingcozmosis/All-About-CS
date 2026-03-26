import discord
from discord.ext import commands
from discord import app_commands

OWNER_ID = 772546626300018699  # 🔥 PUT YOUR DISCORD ID HERE


class Load(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 🔹 LOAD ONLY (OWNER LOCKED)
    @app_commands.command(name="load", description="Load a cog (DEV CMD)")
    async def load(self, interaction: discord.Interaction, cog: str):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message(
                "❌ You are not allowed to use this command.",
                ephemeral=True
            )
            return

        try:
            await self.bot.load_extension(f"cogs.{cog}")
            await interaction.response.send_message(
                f"✅ Loaded `{cog}`",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error loading `{cog}`:\n```{e}```",
                ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(Load(bot))