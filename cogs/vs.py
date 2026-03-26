import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from services.cs2api_service import CS2Service
import asyncio

class PlayerSelect(discord.ui.Select):
    def __init__(self, players, cog, slot):
        self.players = players
        self.cog = cog
        self.slot = slot  # "p1" or "p2"
        
        options = []
        for i, p in enumerate(players[:25]):
            real = f"{p.get('first_name','')} {p.get('last_name','')}".strip()
            desc = real if real else "Unknown name"
            options.append(discord.SelectOption(label=p["nickname"], description=desc, value=str(i)))
        
        super().__init__(placeholder=f"Select {slot} player", options=options)

    async def callback(self, interaction: discord.Interaction):
        player = self.players[int(self.values[0])]
        if self.slot == "p1":
            self.cog._player1_selected = player
        else:
            self.cog._player2_selected = player

        # Fetch stats if both selected
        if getattr(self.cog, "_player1_selected", None) and getattr(self.cog, "_player2_selected", None):
            if not self.cog._stats1 and self.cog._player1_selected.get("slug"):
                try:
                    self.cog._stats1 = await self.cog.cs.get_player_stats(self.cog._player1_selected["slug"])
                except:
                    self.cog._stats1 = {}
            if not self.cog._stats2 and self.cog._player2_selected.get("slug"):
                try:
                    self.cog._stats2 = await self.cog.cs.get_player_stats(self.cog._player2_selected["slug"])
                except:
                    self.cog._stats2 = {}
            embed, view = self.cog.build_vs_embed(
                self.cog._player1_selected,
                self.cog._player2_selected,
                self.cog._stats1,
                self.cog._stats2
            )
            await interaction.response.edit_message(content=None, embed=embed, view=view)
        else:
            await interaction.response.defer()

class PlayerSelectView(discord.ui.View):
    def __init__(self, players1, players2, cog):
        super().__init__(timeout=120)
        # Add select for player1 if multiple
        if isinstance(players1, list) and len(players1) > 1:
            self.add_item(PlayerSelect(players1, cog, "p1"))
        # Add select for player2 if multiple
        if isinstance(players2, list) and len(players2) > 1:
            self.add_item(PlayerSelect(players2, cog, "p2"))

class VSPlayerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cs = CS2Service()
        self._player1_selected = None
        self._player2_selected = None
        self._stats1 = {}
        self._stats2 = {}

    @app_commands.command(name="vs", description="Compare two CS2 pro players")
    async def vs(self, interaction: discord.Interaction, player1: str, player2: str):
        await interaction.response.defer(thinking=True)
        try:
            players1, players2 = await asyncio.gather(
                self.cs.search_player(player1),
                self.cs.search_player(player2)
            )
        except asyncio.TimeoutError:
            await interaction.followup.send("⏱ Player search timed out.")
            return

        if not players1 or not players2:
            await interaction.followup.send("❌ Could not find one of the players.")
            return

        # If multiple results for either, show combined dropdown
        if (isinstance(players1, list) and len(players1) > 1) or (isinstance(players2, list) and len(players2) > 1):
            await interaction.followup.send(
                content="Multiple matches found. Select the correct player for each:",
                view=PlayerSelectView(players1, players2, self)
            )
            # If only one match for either, store it
            if not (isinstance(players1, list) and len(players1) > 1):
                self._player1_selected = players1[0] if isinstance(players1, list) else players1
            if not (isinstance(players2, list) and len(players2) > 1):
                self._player2_selected = players2[0] if isinstance(players2, list) else players2
            return

        # Otherwise, store directly
        self._player1_selected = players1[0] if isinstance(players1, list) else players1
        self._player2_selected = players2[0] if isinstance(players2, list) else players2

        # Fetch stats
        try:
            if self._player1_selected.get("slug"):
                self._stats1 = await self.cs.get_player_stats(self._player1_selected["slug"])
        except:
            self._stats1 = {}
        try:
            if self._player2_selected.get("slug"):
                self._stats2 = await self.cs.get_player_stats(self._player2_selected["slug"])
        except:
            self._stats2 = {}

        embed, view = self.build_vs_embed(
            self._player1_selected,
            self._player2_selected,
            self._stats1,
            self._stats2
        )
        await interaction.followup.send(embed=embed, view=view)

    # --- build_vs_embed stays same as previous, winner calculated KD > Rating > Prize ---
    def build_vs_embed(self, p1, p2, stats1, stats2):
        def get_age(player):
            birth_str = player.get("birthDate")
            if not birth_str: return "N/A"
            try:
                birth = datetime.strptime(birth_str, "%Y-%m-%d")
                today = datetime.today()
                age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
                return str(age)
            except:
                return "N/A"
        def get_real(player):
            if player.get("first_name") and player.get("last_name"):
                return f"{player['first_name']} {player['last_name']}"
            return "Unknown"
        def get_team(player):
            return player.get("team", {}).get("name", "No Team")
        def extract_stats(stats):
            if not stats: return 0,0
            if "results" in stats: stats = stats["results"]
            general = stats.get("general_stats", {})
            kills = general.get("kills_sum",0)
            deaths = general.get("deaths_sum",0)
            kd = round(kills/deaths,2) if deaths>0 else 0
            map_stats = stats.get("map_stats",[])
            rating = round(sum(m.get("avg_player_rating",0) for m in map_stats)/len(map_stats),2) if map_stats else 0
            return kd,rating

        kd1_num,rating1_num=extract_stats(stats1)
        kd2_num,rating2_num=extract_stats(stats2)
        prize1 = p1.get("prize_pool") or 0
        prize2 = p2.get("prize_pool") or 0
        def compare(v1,v2):
            if v1>v2: return f"🟢 {v1}", f"🔴 {v2}"
            elif v2>v1: return f"🔴 {v1}", f"🟢 {v2}"
            else: return f"🟡 {v1}", f"🟡 {v2}"
        kd1,kd2=compare(kd1_num,kd2_num)
        rating1,rating2=compare(rating1_num,rating2_num)
        if prize1>prize2: prize1_str,prize2_str=f"🟢 ${prize1:,}",f"🔴 ${prize2:,}"
        elif prize2>prize1: prize1_str,prize2_str=f"🔴 ${prize1:,}",f"🟢 ${prize2:,}"
        else: prize1_str,prize2_str=f"🟡 ${prize1:,}",f"🟡 ${prize2:,}"

        # Winner logic KD>Rating>Prize
        if kd1_num>kd2_num: winner=p1
        elif kd2_num>kd1_num: winner=p2
        else:
            if rating1_num>rating2_num: winner=p1
            elif rating2_num>rating1_num: winner=p2
            else: winner=p1 if prize1>=prize2 else p2
        winner_text = f"🏆 Winner Stat Wise: {winner['nickname']}"

        embed=discord.Embed(title=winner_text,color=0xff6600)
        embed.add_field(name=p1["nickname"], value=(f"**Real Name:** {get_real(p1)}\n"
                                                    f"**Team:** {get_team(p1)}\n"
                                                    f"**Age:** {get_age(p1)}\n"
                                                    f"**Prize:** {prize1_str}\n"
                                                    f"**KD:** {kd1}\n"
                                                    f"**Rating:** {rating1}"), inline=True)
        embed.add_field(name=p2["nickname"], value=(f"**Real Name:** {get_real(p2)}\n"
                                                    f"**Team:** {get_team(p2)}\n"
                                                    f"**Age:** {get_age(p2)}\n"
                                                    f"**Prize:** {prize2_str}\n"
                                                    f"**KD:** {kd2}\n"
                                                    f"**Rating:** {rating2}"), inline=True)
        if winner.get("image_url"): embed.set_image(url=winner["image_url"])
        view=discord.ui.View()
        if p1.get("slug"): view.add_item(discord.ui.Button(label=f"{p1['nickname']} BO3.gg", url=f"https://bo3.gg/players/{p1['slug']}"))
        if p2.get("slug"): view.add_item(discord.ui.Button(label=f"{p2['nickname']} BO3.gg", url=f"https://bo3.gg/players/{p2['slug']}"))
        embed.set_footer(text="All Things CS • Powered by BO3.gg")
        return embed,view

async def setup(bot):
    await bot.add_cog(VSPlayerCog(bot))