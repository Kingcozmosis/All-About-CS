import discord
from discord.ext import commands
from services.cs2api_service import CS2Service


class LiveMatchCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.cs = CS2Service()

    @discord.app_commands.command(name="live", description="Show current live CS2 matches")
    async def live(self, interaction: discord.Interaction):
        await interaction.response.defer()

        matches = await self.cs.get_live_matches()

        if not matches:
            await interaction.followup.send("❌ No live matches currently.")
            return

        for match in matches:
            team1 = match["team1"]
            team2 = match["team2"]
            score1 = match.get("team1Score", 0)
            score2 = match.get("team2Score", 0)
            map_name = match.get("map", "TBD")
            live_stream = match.get("liveStream")

            embed = discord.Embed(
                title=f"🎮 Live Match: {team1['name']} vs {team2['name']}",
                description=f"**Map:** {map_name}",
                color=discord.Color.orange()
            )

            # Scores
            embed.add_field(
                name="Score",
                value=f"{team1['name']} [{score1}] - [{score2}] {team2['name']}",
                inline=False
            )

            # Logos
            if team1.get("logo"):
                embed.set_thumbnail(url=team1["logo"])
            if team2.get("logo"):
                embed.set_image(url=team2["logo"])

            # Live stream
            if live_stream:
                embed.add_field(
                    name="🔴 Live Stream",
                    value=f"[Watch Here]({live_stream})",
                    inline=False
                )

            # Buttons
            view = discord.ui.View()
            if match.get("hltvId"):
                view.add_item(discord.ui.Button(
                    label="HLTV Match Page",
                    url=f"https://www.hltv.org/matches/{match['hltvId']}/"
                ))
            if match.get("bo3Slug"):
                view.add_item(discord.ui.Button(
                    label="BO3 Match Page",
                    url=f"https://bo3.gg/matches/{match['bo3Slug']}"
                ))

            await interaction.followup.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(LiveMatchCog(bot))