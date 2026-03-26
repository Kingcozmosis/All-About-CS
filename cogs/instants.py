import discord
from discord.ext import commands
from discord import app_commands
import os

ASSETS_DIR = "assets/instants"  # Your folder with smoke images


class InstantsView(discord.ui.View):
    def __init__(self, bot, file_structure):
        super().__init__(timeout=300)
        self.bot = bot
        self.file_structure = file_structure  # dict of map → side → location → filename
        self.selected_map = None
        self.selected_side = None

        # 1️⃣ Map select
        map_select = discord.ui.Select(
            placeholder="Select a map",
            options=[
                discord.SelectOption(label=map_name) for map_name in sorted(file_structure.keys())
            ],
            min_values=1,
            max_values=1
        )
        map_select.callback = self.map_callback
        self.add_item(map_select)

    async def map_callback(self, interaction: discord.Interaction):
        self.selected_map = interaction.data["values"][0]
        side_structure = self.file_structure[self.selected_map]

        # Remove old side/location selects
        self.clear_items()
        # Add map select back
        map_select = discord.ui.Select(
            placeholder="Select a map",
            options=[
                discord.SelectOption(label=self.selected_map, default=True)
            ],
            min_values=1,
            max_values=1
        )
        self.add_item(map_select)

        # 2️⃣ Side select
        side_select = discord.ui.Select(
            placeholder="Select a side",
            options=[
                discord.SelectOption(label=side) for side in sorted(side_structure.keys())
            ],
            min_values=1,
            max_values=1
        )
        side_select.callback = self.side_callback
        self.add_item(side_select)

        await interaction.response.edit_message(view=self)

    async def side_callback(self, interaction: discord.Interaction):
        self.selected_side = interaction.data["values"][0]
        location_structure = self.file_structure[self.selected_map][self.selected_side]

        # Remove old location select if exists
        self.clear_items()
        # Add map and side selects back
        map_select = discord.ui.Select(
            placeholder="Select a map",
            options=[discord.SelectOption(label=self.selected_map, default=True)],
            min_values=1,
            max_values=1
        )
        side_select = discord.ui.Select(
            placeholder="Select a side",
            options=[discord.SelectOption(label=self.selected_side, default=True)],
            min_values=1,
            max_values=1
        )
        self.add_item(map_select)
        self.add_item(side_select)

        # 3️⃣ Location select
        location_select = discord.ui.Select(
            placeholder="Select a location",
            options=[
                discord.SelectOption(label=loc) for loc in sorted(location_structure.keys())
            ],
            min_values=1,
            max_values=1
        )
        location_select.callback = self.location_callback
        self.add_item(location_select)

        await interaction.response.edit_message(view=self)

    async def location_callback(self, interaction: discord.Interaction):
        location = interaction.data["values"][0]
        filename = self.file_structure[self.selected_map][self.selected_side][location]
        file_path = os.path.join(ASSETS_DIR, filename)

        embed = discord.Embed(
            title=f"{self.selected_map.upper()} {self.selected_side.upper()} - {location.upper()} Insta Smokes",
            color=0xff6600
        )
        embed.set_image(url=f"attachment://{filename}")
        embed.set_footer(text="All Things CS • Powered by BO3.gg")

        await interaction.response.send_message(embed=embed, file=discord.File(file_path))


class Instants(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.file_structure = self.scan_files()

    def scan_files(self):
        """
        Scan the assets folder and build structure:
        map -> side -> location -> filename
        """
        structure = {}
        for file in os.listdir(ASSETS_DIR):
            if not file.lower().endswith((".png", ".jpg", ".jpeg")):
                continue
            parts = file[:-4].lower().split("-")  # remove extension and split
            if len(parts) != 3:
                continue
            side, location, map_name = parts
            structure.setdefault(map_name, {}).setdefault(side, {})[location] = file
        return structure

    @app_commands.command(name="instants", description="View CS2 smoke lineups")
    async def instants(self, interaction: discord.Interaction):
        if not self.file_structure:
            await interaction.response.send_message(
                "No smoke images found. The Dev Will Add More Soon!", ephemeral=True
            )
            return
        await interaction.response.send_message(
            "Select your smoke lineup:", view=InstantsView(self.bot, self.file_structure)
        )


async def setup(bot):
    await bot.add_cog(Instants(bot))