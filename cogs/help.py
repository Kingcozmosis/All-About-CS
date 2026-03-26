import discord
from discord.ext import commands
from discord import app_commands

OWNER_ID = 772546626300018699


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="help",
        description="View all All Things CS commands"
    )
    async def help(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title="All Things CS Commands",
            description=(
                "Here are all available commands.\n\n"
                "💬 **Did you know you can also @mention the bot with any Counter-Strike question** "
                "and it will reply using AI.\n\n"
                "Example:\n"
                "`@All Things CS What is a full buy?`"
            ),
            color=0xff6600
        )

        embed.set_author(
            name="All Things CS • Powered by BO3.gg",
            icon_url=self.bot.user.display_avatar.url,
            url="https://bo3.gg"
        )

        general_cmds = []
        admin_cmds = []
        dev_cmds = []

        for command in self.bot.tree.walk_commands():
            name = f"/{command.name}"
            desc = command.description or "No description"
            desc_lower = desc.lower()

            # Hide dev command from everyone except you
            if command.name == "load":
                if interaction.user.id == OWNER_ID:
                    dev_cmds.append((name, desc))
                continue

            # Separate admin commands properly
            if "admin" in desc_lower:
                admin_cmds.append((name, desc))
            else:
                general_cmds.append((name, desc))

        general_cmds.sort()
        admin_cmds.sort()
        dev_cmds.sort()

        if general_cmds:
            value = "\n".join(
                [f"**{name}** — {desc}" for name, desc in general_cmds]
            )
            embed.add_field(
                name="Commands",
                value=value,
                inline=False
            )

        if admin_cmds:
            value = "\n".join(
                [f"**{name}** — {desc}" for name, desc in admin_cmds]
            )
            embed.add_field(
                name="Admin Commands",
                value=value,
                inline=False
            )

        if interaction.user.id == OWNER_ID and dev_cmds:
            value = "\n".join(
                [f"**{name}** — {desc}" for name, desc in dev_cmds]
            )
            embed.add_field(
                name="Developer Commands",
                value=value,
                inline=False
            )

        embed.add_field(
            name="",
            value=(
                "All was made possible by the good friends at "
                "[**BO3.gg**](https://bo3.gg), Redefining the gaming portal experience."
            ),
            inline=False
        )

        embed.set_footer(
            text="All Things CS • Powered By BO3.GG"
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(HelpCog(bot))