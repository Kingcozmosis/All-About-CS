import discord
from discord.ext import commands
from services.cs2api_service import CS2Service


class TeamCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.cs2 = CS2Service()

    @discord.app_commands.command(name="team", description="Show A CS2 team roster")
    async def team(self, interaction: discord.Interaction, name: str):

        await interaction.response.defer()

        team = await self.cs2.search_team(name)

        if not team:
            await interaction.followup.send("❌ Team not found.")
            return

        embed = discord.Embed(
            title=f"🏆 {team['name']}",
            description="Professional Counter-Strike Team",
            color=discord.Color.red()
        )

        # Team logo
        if team.get("logo"):
            embed.set_thumbnail(url=team["logo"])

        # World ranking link (HLTV)
        embed.add_field(
            name="🌍 World Rankings",
            value="[View HLTV World Rankings](https://www.hltv.org/ranking/teams)",
            inline=True
        )

        # Roster
        roster = team.get("roster", [])
        if roster:
            roster_text = "\n".join([f"• {player}" for player in roster])
        else:
            roster_text = "Roster not available."

        embed.add_field(
            name="👥 Current Roster",
            value=roster_text,
            inline=False
        )

        # Buttons
        view = discord.ui.View()

        # HLTV team search
        hltv_url = f"https://www.hltv.org/search?query={team['name']}"
        view.add_item(
            discord.ui.Button(
                label="HLTV Page",
                url=hltv_url
            )
        )

        # BO3 team page
        if team.get("slug"):
            bo3_url = f"https://bo3.gg/teams/{team['slug']}"
            view.add_item(
                discord.ui.Button(
                    label="BO3 Team Page",
                    url=bo3_url
                )
            )

        embed.set_footer(text="All Things CS • Powered by BO3.gg")

        await interaction.followup.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(TeamCog(bot))