import discord
from discord.ext import commands
from discord import app_commands
from services.rss_tracker import get_latest_steamdb

class SteamDB(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="steamdb", description="Latest CS2 update")
    async def steamdb(self, interaction: discord.Interaction):

        update = get_latest_steamdb()

        embed = discord.Embed(
            title="Latest Counter-Strike 2 Update",
            url=update["link"],
            description=update["title"],
            color=0xe67e22
        )

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(SteamDB(bot))