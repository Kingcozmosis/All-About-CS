import discord
from discord.ext import commands
from discord import app_commands
import os

CALLOUTS_FOLDER = "assets/callouts"  # Folder where all your map images live

class Callouts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.maps = self.load_maps()  # Auto-load available maps

    def load_maps(self):
        """Scan the callouts folder and return available map names without extensions."""
        maps = {}
        for filename in os.listdir(CALLOUTS_FOLDER):
            if filename.lower().endswith((".png", ".jpg", ".jpeg")):
                map_name = os.path.splitext(filename)[0].lower()  # strip extension
                maps[map_name] = filename
        return maps

    @app_commands.command(name="callouts", description="View map callouts")
    async def callouts(self, interaction: discord.Interaction):
        if not self.maps:
            await interaction.response.send_message("❌ No callouts found.", ephemeral=True)
            return

        # Create dropdown menu options
        options = [
            discord.SelectOption(label=map_name.capitalize())
            for map_name in sorted(self.maps.keys())
        ]

        # Define the dropdown
        class MapSelect(discord.ui.View):
            def __init__(self, parent):
                super().__init__(timeout=60)
                self.parent = parent

                select = discord.ui.Select(
                    placeholder="Choose a map",
                    options=options,
                    min_values=1,
                    max_values=1
                )
                select.callback = self.select_callback
                self.add_item(select)

            async def select_callback(self, select_interaction: discord.Interaction):
                map_choice = select_interaction.data["values"][0].lower()
                file_name = self.parent.maps.get(map_choice)
                if not file_name:
                    await select_interaction.response.send_message(
                        f"❌ No callout found for `{map_choice}`", ephemeral=True
                    )
                    return

                file_path = os.path.join(CALLOUTS_FOLDER, file_name)
                if not os.path.exists(file_path):
                    await select_interaction.response.send_message(
                        f"❌ File not found for `{map_choice}`", ephemeral=True
                    )
                    return

                # Create embed
                embed = discord.Embed(
                    title=f"{map_choice.capitalize()} Callouts",
                    color=0xff6600
                )
                file = discord.File(file_path, filename=file_name)
                embed.set_image(url=f"attachment://{file_name}")
                embed.set_footer(text="All Things CS • Powered by BO3.gg")

                await select_interaction.response.send_message(
                    embed=embed,
                    file=file
                )

        # Send the dropdown
        await interaction.response.send_message(
            "Select a map to view its callouts:",
            view=MapSelect(self),
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Callouts(bot))