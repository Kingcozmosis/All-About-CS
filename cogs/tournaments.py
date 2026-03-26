import discord
from discord.ext import commands
from discord import app_commands
from services.cs2api_service import CS2Service
import asyncio


class Tournaments(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cs2_service = CS2Service()

    def normalize_matches(self, data):
        if data is None:
            return []
        if isinstance(data, dict):
            return data.get("results", [])
        if isinstance(data, list):
            return data
        return []

    @app_commands.command(
        name="tournaments",
        description="View live CS tournaments"
    )
    async def tournaments(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            live_raw = await asyncio.wait_for(
                self.cs2_service.get_live_matches(),
                timeout=10
            )
        except asyncio.TimeoutError:
            await interaction.followup.send("Timed out fetching live tournaments.")
            return
        except Exception as e:
            await interaction.followup.send(f"Error fetching live tournaments: {e}")
            return

        live_matches = self.normalize_matches(live_raw)

        tournaments = {}

        for match in live_matches:
            tournament_data = match.get("tournament", {}) or {}
            tournament_name = tournament_data.get("name", "Unknown Tournament")

            if tournament_name not in tournaments:
                tournaments[tournament_name] = {
                    "name": tournament_name,
                    "matches": 0
                }

            tournaments[tournament_name]["matches"] += 1

        if not tournaments:
            await interaction.followup.send("No live tournaments found right now.")
            return

        sorted_tournaments = sorted(
            tournaments.values(),
            key=lambda t: (-t["matches"], t["name"].lower())
        )

        embed = discord.Embed(
            title="Live CS2 Tournaments",
            description="Showing tournaments with live matches right now",
            color=discord.Color.green()
        )

        for tournament in sorted_tournaments[:10]:
            embed.add_field(
                name=f"🟢 {tournament['name']}",
                value=f"Matches Live: {tournament['matches']}",
                inline=False
            )

        extra_count = len(sorted_tournaments) - 10
        if extra_count > 0:
            embed.set_footer(
                text=f"All Things CS • Powered by BO3.gg • {extra_count} more not shown"
            )
        else:
            embed.set_footer(text="All Things CS • Powered by BO3.gg")

        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                label="View All Tournaments",
                style=discord.ButtonStyle.link,
                url="https://bo3.gg/tournaments/current"
            )
        )

        await interaction.followup.send(embed=embed, view=view)

    async def cog_unload(self):
        await self.cs2_service.close()


async def setup(bot):
    await bot.add_cog(Tournaments(bot))