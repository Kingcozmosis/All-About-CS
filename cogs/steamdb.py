import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiohttp
import json
import os

APP_ID = 730
API_URL = f"https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid={APP_ID}&count=5"

CONFIG_FILE = "data/steamdb_config.json"


class SteamDBCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.check_updates.start()

    # -------------------------
    # Config
    # -------------------------

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            return {}

        with open(CONFIG_FILE, "r") as f:
            return json.load(f)

    def save_config(self, data):
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=4)

    # -------------------------
    # Enable SteamDB updates
    # -------------------------

    @app_commands.command(
        name="steamdb",
        description="Enable CS2 Steam update notifications"
    )
    async def steamdb(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        role: discord.Role = None
    ):

        config = self.load_config()

        config[str(interaction.guild.id)] = {
            "channel": channel.id,
            "role": role.id if role else None,
            "last_post": None
        }

        self.save_config(config)

        msg = f"✅ CS2 Steam updates enabled in {channel.mention}"
        if role:
            msg += f"\nRole ping: {role.mention}"

        await interaction.response.send_message(msg)

    # -------------------------
    # Disable
    # -------------------------

    @app_commands.command(
        name="steamdb_off",
        description="Disable CS2 Steam update notifications"
    )
    async def steamdb_off(self, interaction: discord.Interaction):

        config = self.load_config()

        if str(interaction.guild.id) in config:
            del config[str(interaction.guild.id)]
            self.save_config(config)

            await interaction.response.send_message("🛑 Steam updates disabled.")
        else:
            await interaction.response.send_message("❌ Steam updates were not enabled.")

    # -------------------------
    # Test command
    # -------------------------

    @app_commands.command(
        name="steamdb_test",
        description="Test the CS2 update system"
    )
    async def steamdb_test(self, interaction: discord.Interaction):

        await interaction.response.defer()

        config = self.load_config()

        if str(interaction.guild.id) not in config:
            await interaction.followup.send("❌ Steam updates are not enabled.")
            return

        news = await self.fetch_news()

        if not news:
            await interaction.followup.send("❌ Could not fetch Steam updates.")
            return

        article = news[0]

        channel = self.bot.get_channel(config[str(interaction.guild.id)]["channel"])

        await self.send_update(channel, article, config[str(interaction.guild.id)])

        await interaction.followup.send("✅ Test update posted.")

    # -------------------------
    # Fetch Steam News
    # -------------------------

    async def fetch_news(self):

        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL) as resp:

                data = await resp.json()

                return data["appnews"]["newsitems"]

    # -------------------------
    # Send embed
    # -------------------------

    async def send_update(self, channel, article, guild_config):

        role_ping = ""
        if guild_config.get("role"):
            role_ping = f"<@&{guild_config['role']}>"

        embed = discord.Embed(
            title=article["title"],
            url=article["url"],
            description=article["contents"][:400] + "...",
            color=0x1b2838
        )

        embed.set_author(
            name="Counter-Strike 2 Update",
            icon_url="https://steamcdn-a.akamaihd.net/steam/apps/730/header.jpg"
        )

        embed.set_footer(text="Steam Updates • AppID 730")

        await channel.send(content=role_ping, embed=embed)

    # -------------------------
    # Background checker
    # -------------------------

    @tasks.loop(minutes=5)
    async def check_updates(self):

        config = self.load_config()

        if not config:
            return

        news = await self.fetch_news()

        if not news:
            return

        newest = news[0]

        for guild_id, guild_config in config.items():

            if guild_config["last_post"] == newest["gid"]:
                continue

            channel = self.bot.get_channel(guild_config["channel"])

            if not channel:
                continue

            try:

                await self.send_update(channel, newest, guild_config)

                config[guild_id]["last_post"] = newest["gid"]
                self.save_config(config)

            except Exception as e:
                print("Steam update error:", e)

    # -------------------------

    @check_updates.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(SteamDBCog(bot))