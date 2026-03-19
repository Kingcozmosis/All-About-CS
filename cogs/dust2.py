import discord
from discord.ext import commands
from discord import app_commands
from services.rss_tracker import get_latest_dust2

class Dust2(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="dust2", description="Latest Dust2.us article")
    async def dust2(self, interaction: discord.Interaction):

        article = get_latest_dust2()

        embed = discord.Embed(
            title=article["title"],
            url=article["link"],
            description="Latest Dust2.us article",
            color=0x2ecc71
        )

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Dust2(bot))