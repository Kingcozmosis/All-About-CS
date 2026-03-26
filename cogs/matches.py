import discord
from discord.ext import commands
from discord import app_commands
from services.cs2api_service import CS2Service
import asyncio


class Matches(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cs2_service = CS2Service()

    @app_commands.command(name="matches", description="View today's or live CS matches")
    async def matches(self, interaction: discord.Interaction):
        await interaction.response.defer()

        matches_list = []

        # 1️⃣ Try today's scheduled matches
        try:
            matches = await asyncio.wait_for(self.cs2_service.get_todays_matches(), timeout=10)
        except asyncio.TimeoutError:
            await interaction.followup.send("Timed out fetching today's matches.")
            return
        except Exception as e:
            await interaction.followup.send(f"Error fetching today's matches: {e}")
            return

        if matches is None:
            matches_list = []
        elif isinstance(matches, dict):
            matches_list = matches.get("results", [])
        elif isinstance(matches, list):
            matches_list = matches
        else:
            matches_list = []

        # 2️⃣ Fallback to live matches
        if not matches_list:
            try:
                live_matches = await asyncio.wait_for(self.cs2_service.get_live_matches(), timeout=10)
            except asyncio.TimeoutError:
                await interaction.followup.send("Timed out fetching live matches.")
                return
            except Exception as e:
                await interaction.followup.send(f"Error fetching live matches: {e}")
                return

            if live_matches is None:
                matches_list = []
            elif isinstance(live_matches, dict):
                matches_list = live_matches.get("results", [])
            elif isinstance(live_matches, list):
                matches_list = live_matches
            else:
                matches_list = []

        view = discord.ui.View()

        # Button for tomorrow matches
        button_tomorrow = discord.ui.Button(
            label="View Tomorrow's Matches",
            style=discord.ButtonStyle.link,
            url="https://bo3.gg/matches"
        )
        view.add_item(button_tomorrow)

        if not matches_list:
            await interaction.followup.send(
                "No matches found for today or live right now.",
                view=view
            )
            return

        # 3️⃣ Build embed
        embed = discord.Embed(
            title="Current CS Matches",
            description="Showing up to 10 matches",
            color=discord.Color.green()
        )

        for match in matches_list[:10]:

            team1 = match.get("team1", {})
            team2 = match.get("team2", {})

            team1_name = team1.get("name", "TBD")
            team2_name = team2.get("name", "TBD")

            tournament = match.get("tournament", {}).get("name", "Unknown Tournament")

            match_slug = match.get("slug")
            bo3_link = f"https://bo3.gg/matches/{match_slug}" if match_slug else None

            field_value = f"Tournament: {tournament}"

            if bo3_link:
                field_value += f"\nWatch Match: [View Match]({bo3_link})"

            embed.add_field(
                name=f"{team1_name} vs {team2_name}",
                value=field_value,
                inline=False
            )

        # 4️⃣ View more button
        extra_matches = len(matches_list) - 10

        if extra_matches > 0:
            button_more = discord.ui.Button(
                label=f"View More Matches ({extra_matches} more)",
                style=discord.ButtonStyle.link,
                url="https://bo3.gg/matches"
            )
            view.add_item(button_more)
            
        embed.set_footer(text="All Things CS • Powered by BO3.gg")
        await interaction.followup.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Matches(bot))