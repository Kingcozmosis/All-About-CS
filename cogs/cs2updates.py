import discord
from discord.ext import commands, tasks
from discord import app_commands
import feedparser
import json
import os
import re

RSS_URL = "https://steamcommunity.com/games/CSGO/rss/"
CONFIG_FILE = "data/cs2updates_config.json"

# Working images for embeds
CS2_LOGO = "https://upload.wikimedia.org/wikipedia/en/thumb/6/6c/Counter-Strike_2_cover_art.jpg/512px-Counter-Strike_2_cover_art.jpg"
CS2_BANNER = "https://cdn.akamai.steamstatic.com/apps/csgo/images/csgo_react/social/cs2.jpg"


class CS2UpdatesCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.check_updates.start()

    # -------------------------
    # Config handling
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
    # Enable updates
    # -------------------------
    @app_commands.command(
        name="cs2updates",
        description="Enable CS2 update posts"
    )
    async def cs2updates(
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

        msg = f"✅ CS2 updates enabled in {channel.mention}"

        if role:
            msg += f"\nRole ping: {role.mention}"

        await interaction.response.send_message(msg)

    # -------------------------
    # Disable updates
    # -------------------------
    @app_commands.command(
        name="cs2updates_off",
        description="Disable CS2 updates"
    )
    async def cs2updates_off(self, interaction: discord.Interaction):

        config = self.load_config()

        if str(interaction.guild.id) in config:

            del config[str(interaction.guild.id)]
            self.save_config(config)

            await interaction.response.send_message(
                "🛑 CS2 updates disabled."
            )

        else:
            await interaction.response.send_message(
                "❌ CS2 updates were not enabled."
            )

    # -------------------------
    # Clean HTML from Steam
    # -------------------------
    def clean_html(self, text):

        text = re.sub("<.*?>", "", text)
        text = text.replace("[", "\n**[")
        text = text.replace("]", "]**\n")

        return text.strip()

    # -------------------------
    # Test command
    # -------------------------
    @app_commands.command(
        name="cs2updates_test",
        description="Post the latest CS2 update"
    )
    async def cs2updates_test(self, interaction: discord.Interaction):

        await interaction.response.defer()

        config = self.load_config()

        if str(interaction.guild.id) not in config:
            await interaction.followup.send(
                "❌ CS2 updates not enabled in this server."
            )
            return

        feed = feedparser.parse(RSS_URL)

        if not feed.entries:
            await interaction.followup.send(
                "❌ Could not find a CS2 update."
            )
            return

        entry = feed.entries[0]

        update = {
            "title": entry.title,
            "link": entry.link,
            "text": self.clean_html(entry.summary)
        }

        channel = self.bot.get_channel(
            config[str(interaction.guild.id)]["channel"]
        )

        await self.send_update(channel, update, config[str(interaction.guild.id)])

        await interaction.followup.send("✅ Test update posted.")

    # -------------------------
    # Send update embed
    # -------------------------
    async def send_update(self, channel, update, guild_config):

        role_ping = ""
        if guild_config.get("role"):
            role_ping = f"<@&{guild_config['role']}>"

        embed = discord.Embed(
            title=update["title"],
            url=update["link"],
            description=update["text"],
            color=0xff6600
        )

        # CS2 logo top-right
        embed.set_thumbnail(url=CS2_LOGO)

        # banner image below text
        embed.set_image(url=CS2_BANNER)

        embed.set_footer(text="Source: Steam Community • All Things CS • Powered by BO3.gg")

        view = discord.ui.View()

        view.add_item(
            discord.ui.Button(
                label="View Full Update",
                url=update["link"]
            )
        )

        await channel.send(
            content=role_ping,
            embed=embed,
            view=view
        )

    # -------------------------
    # Background checker
    # -------------------------
    @tasks.loop(minutes=5)
    async def check_updates(self):

        config = self.load_config()

        if not config:
            return

        feed = feedparser.parse(RSS_URL)

        if not feed.entries:
            return

        newest = feed.entries[0]

        update = {
            "title": newest.title,
            "link": newest.link,
            "text": self.clean_html(newest.summary)
        }

        for guild_id, guild_config in config.items():

            last_post = guild_config.get("last_post")

            if last_post == newest.link:
                continue

            channel = self.bot.get_channel(guild_config["channel"])

            if not channel:
                continue

            try:

                await self.send_update(channel, update, guild_config)

                config[guild_id]["last_post"] = newest.link
                self.save_config(config)

            except Exception as e:
                print(f"CS2 update error: {e}")

    # -------------------------
    # Wait until bot ready
    # -------------------------
    @check_updates.before_loop
    async def before_updates(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(CS2UpdatesCog(bot))