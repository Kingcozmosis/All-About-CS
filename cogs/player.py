import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from services.cs2api_service import CS2Service


class PlayerCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.cs = CS2Service()

    @app_commands.command(name="player", description="Search for a CS2 pro player")
    async def player(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer()

        player = await self.cs.search_player(name)

        if not player:
            await interaction.followup.send("❌ This player is not a pro.")
            return

        # Player full name
        real_name = ""
        if player.get("first_name") and player.get("last_name"):
            real_name = f"{player['first_name']} {player['last_name']}"

        title = player["nickname"]
        if real_name:
            title = f"{player['nickname']} — {real_name}"

        embed = discord.Embed(title=title, color=0xff6600)

        # Country
        country_name = player.get("country", {}).get("name") if isinstance(player.get("country"), dict) else player.get("country")
        country_name = country_name or "N/A"
        embed.add_field(name="🌍 Country", value=country_name, inline=True)

        # Team
        team = player.get("team", {})
        team_name = team.get("name") if isinstance(team, dict) else team
        team_name = team_name or "No Team"
        embed.add_field(name="🏆 Team", value=team_name, inline=True)

        # Age
        age_text = "N/A"
        birth_str = player.get("birthDate")
        if birth_str:
            try:
                birth = datetime.strptime(birth_str, "%Y-%m-%d")
                today = datetime.today()
                age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
                age_text = str(age)
            except Exception:
                pass
        embed.add_field(name="🎂 Age", value=age_text, inline=True)

        # Time on Team (years, months, days)
        time_on_team_text = "N/A"
        stats = player.get("stats", {})
        if stats and stats.get("time_on_team"):
            try:
                # Expecting "YYYY-MM-DD" start date in stats["time_on_team"]
                start_date_str = stats["time_on_team"]
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                today = datetime.today()

                years = today.year - start_date.year
                months = today.month - start_date.month
                days = today.day - start_date.day

                if days < 0:
                    months -= 1
                    last_month = (today.month - 1) if today.month > 1 else 12
                    year_for_last_month = today.year if today.month > 1 else today.year - 1
                    days_in_last_month = (datetime(year_for_last_month, last_month + 1, 1) - datetime(year_for_last_month, last_month, 1)).days
                    days += days_in_last_month

                if months < 0:
                    years -= 1
                    months += 12

                time_on_team_text = f"{years}y {months}m {days}d"
            except Exception:
                time_on_team_text = stats["time_on_team"]  # fallback if not a date
        embed.add_field(name="⏱ Time on Team", value=time_on_team_text, inline=True)

        # Total prize money
        prize_val = player.get("prize_pool")
        prize_text = f"${prize_val:,}" if prize_val is not None else "N/A"
        embed.add_field(name="💰 Total Prize", value=prize_text, inline=True)

        # Player image
        if player.get("image_url"):
            embed.set_thumbnail(url=player["image_url"])

        # Buttons view
        view = discord.ui.View()
        hltv_url = f"https://www.hltv.org/search?query={player['nickname']}"
        view.add_item(discord.ui.Button(label="HLTV Profile", url=hltv_url))
        if player.get("steam_link"):
            view.add_item(discord.ui.Button(label="Steam Profile", url=player["steam_link"]))

        embed.set_footer(text="All Things CS • Powered by BO3.gg")
        await interaction.followup.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(PlayerCog(bot))