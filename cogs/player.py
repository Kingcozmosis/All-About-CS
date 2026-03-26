import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from services.cs2api_service import CS2Service
from services.steam_ids import STEAM_IDS
import asyncio
import os


class PlayerSelect(discord.ui.Select):
    def __init__(self, players, cog):
        self.players = players
        self.cog = cog

        options = []
        for i, p in enumerate(players[:25]):
            real = ""
            if p.get("first_name") and p.get("last_name"):
                real = f"{p['first_name']} {p['last_name']}"
            label = p["nickname"]
            desc = real if real else "Unknown name"
            options.append(discord.SelectOption(label=label, description=desc, value=str(i)))

        super().__init__(placeholder="Select the correct player", options=options)

    async def callback(self, interaction: discord.Interaction):
        player = self.players[int(self.values[0])]
        embed, view, file = self.cog.build_player_embed(player)

        if file:
            await interaction.response.edit_message(
                content=None,
                embed=embed,
                view=view,
                attachments=[file]
            )
        else:
            await interaction.response.edit_message(
                content=None,
                embed=embed,
                view=view
            )


class PlayerSelectView(discord.ui.View):
    def __init__(self, players, cog):
        super().__init__(timeout=120)
        self.add_item(PlayerSelect(players, cog))


class PlayerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cs = CS2Service()

    # --------------------------
    # FILE PATH
    # --------------------------
    def get_washee_image_path(self):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(project_root, "assets", "players", "washee_washee.jpg")

    # --------------------------
    # EASTER EGG PLAYER
    # --------------------------
    def get_washee_player(self):
        player = {
            "nickname": "Mr Washee Washee",
            "first_name": "室因",
            "last_name": "帕克",
            "country": "🇨🇳 China",
            "region": "Asia",
            "steam_link": None,
            "image_url": None,
            "local_image": self.get_washee_image_path(),
            "slug": "mrwasheewashee",
            "birthDate": "1974-01-01",
            "team": {
                "name": "CCP",
                "slug": None,
                "logo": None,
                "time_on_team": "52 years"
            },
            "stats": {
                "time_on_team": "52 years"
            },
            "prize_pool": "¥478,273,950,000"
        }

        # ✅ REAL steam link from your config
        if "mrwasheewashee" in STEAM_IDS:
            player["steam_link"] = f"https://steamcommunity.com/profiles/{STEAM_IDS['mrwasheewashee']}"

        return player

    # --------------------------
    # COMMAND
    # --------------------------
    @app_commands.command(name="player", description="Search for a CS2 pro player")
    async def player(self, interaction: discord.Interaction, name: str):
        await interaction.response.send_message(f"🔎 Searching for player **{name}**...")
        loading_msg = await interaction.original_response()

        normalized_name = (
            name.lower()
            .strip()
            .replace(" ", "")
            .replace("-", "")
            .replace("_", "")
        )

        # 🔥 EASTER EGG TRIGGER (NO API CALL)
        if normalized_name == "mrwasheewashee":
            player = self.get_washee_player()
            embed, view, file = self.build_player_embed(player)

            try:
                await loading_msg.delete()
            except:
                pass

            if file:
                await interaction.followup.send(embed=embed, view=view, file=file)
            else:
                await interaction.followup.send(embed=embed, view=view)
            return

        # --------------------------
        # NORMAL FLOW
        # --------------------------
        try:
            task = asyncio.create_task(self.cs.search_player(name))
            players = await asyncio.wait_for(task, timeout=10)
        except asyncio.TimeoutError:
            task.cancel()
            await loading_msg.edit(
                content="⏱ Player search timed out after **10 seconds**.\n"
                        "The player may not exist or try checking your spelling."
            )
            return

        if not players:
            await loading_msg.edit(content="❌ This player is not a pro.")
            return

        if isinstance(players, list) and len(players) > 1:
            await loading_msg.edit(
                content="Multiple players found. Select the correct player:",
                view=PlayerSelectView(players, self)
            )
            return

        player = players[0] if isinstance(players, list) else players
        embed, view, file = self.build_player_embed(player)

        if file:
            await loading_msg.edit(content=None, embed=embed, view=view, attachments=[file])
        else:
            await loading_msg.edit(content=None, embed=embed, view=view)

    # --------------------------
    # EMBED BUILDER
    # --------------------------
    def build_player_embed(self, player):
        normalized_nickname = (
            str(player.get("nickname", ""))
            .lower()
            .replace(" ", "")
        )
        is_washee = normalized_nickname == "mrwasheewashee"

        real_name = ""
        if player.get("first_name") and player.get("last_name"):
            real_name = f"{player['first_name']} {player['last_name']}"

        title = f"{player['nickname']} — {real_name}" if real_name else player["nickname"]
        embed = discord.Embed(title=title, color=0xff6600)

        # COUNTRY (FIXED)
        if is_washee:
            country_name = "🇨🇳 China"
        else:
            country = player.get("country")
            country_name = country if isinstance(country, str) else "N/A"

        embed.add_field(name="🌍 Country", value=country_name, inline=True)

        # TEAM
        team = player.get("team") or {}
        embed.add_field(name="🏆 Team", value=team.get("name", "No Team"), inline=True)

        # AGE
        if is_washee:
            age_text = "52"
        else:
            age_text = "N/A"
            birth_str = player.get("birthDate")
            if birth_str:
                try:
                    birth = datetime.strptime(birth_str, "%Y-%m-%d")
                    today = datetime.today()
                    age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
                    age_text = str(age)
                except:
                    pass

        embed.add_field(name="🎂 Age", value=age_text, inline=True)

        # TIME ON TEAM
        time_on_team = player.get("stats", {}).get("time_on_team", "N/A")
        embed.add_field(name="⏱ Time on Team", value=time_on_team, inline=True)

        # PRIZE
        prize_val = player.get("prize_pool")
        if isinstance(prize_val, str):
            prize_text = prize_val
        elif prize_val:
            prize_text = f"${prize_val:,}"
        else:
            prize_text = "N/A"

        embed.add_field(name="💰 Total Prize", value=prize_text, inline=True)

        # IMAGE (FIXED)
        file = None
        local_image = player.get("local_image")

        if local_image and os.path.isfile(local_image):
            file = discord.File(local_image, filename="washee.jpg")
            embed.set_thumbnail(url="attachment://washee.jpg")
        elif player.get("image_url"):
            embed.set_thumbnail(url=player["image_url"])

        # BUTTONS
        view = discord.ui.View()

        if is_washee:
            view.add_item(discord.ui.Button(
                label="HLTV Profile",
                url="https://www.hltv.org/player/99999/mr-washee-washee"
            ))

            if player.get("steam_link"):
                view.add_item(discord.ui.Button(
                    label="Steam Profile",
                    url=player["steam_link"]
                ))

            view.add_item(discord.ui.Button(
                label="BO3.gg Profile",
                url="https://bo3.gg/players/mrwasheewashee"
            ))

        else:
            view.add_item(discord.ui.Button(
                label="HLTV Profile",
                url=f"https://www.hltv.org/search?query={player['nickname']}"
            ))

            if player.get("steam_link"):
                view.add_item(discord.ui.Button(
                    label="Steam Profile",
                    url=player["steam_link"]
                ))

            if player.get("slug"):
                view.add_item(discord.ui.Button(
                    label="BO3.gg Profile",
                    url=f"https://bo3.gg/players/{player['slug']}"
                ))

        embed.set_footer(text="All Things CS • Powered by BO3.gg")
        return embed, view, file


async def setup(bot):
    await bot.add_cog(PlayerCog(bot))