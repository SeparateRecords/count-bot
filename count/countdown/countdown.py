from __future__ import annotations

from pathlib import Path

import discord.ext.commands as commands

from count.countdown.assets import config_to_assets
from count.countdown.cog_creation import COG_NAME, create_commands_cog
from count.errors import fail


class CountdownManagement(commands.Cog, name="Countdown Management"):
    """Manage the dynamically generated commands for counting."""

    def __init__(
        self,
        bot: commands.Bot,
        config_path: Path,
    ) -> None:
        self.bot = bot
        self.config_path = config_path
        self.add_commands_to_bot()

    def cog_unload(self):
        """Removes the generated cog when this cog is unloaded."""
        self.bot.remove_cog(COG_NAME)

    def add_commands_to_bot(self):
        """Generates the cog and registers it to the bot.

        If the cog is already loaded, it will be unloaded first.
        """
        # This goes first so that if it fails (for some reason)
        # then nothing will be changed.
        cog = self.create_cog()
        self.bot.remove_cog(COG_NAME)
        self.bot.add_cog(cog)

    def create_cog(self):
        """Creates the cog from the stored config."""
        assets = config_to_assets(self.config_path)
        cog = create_commands_cog(assets)
        return cog

    @commands.command(name="reload-count-commands")
    @commands.is_owner()
    async def reload_count_commands(self, ctx: commands.Context):
        try:
            self.add_commands_to_bot()
        except Exception as e:
            fail("Unable to reload the commands.", cause=e)
        else:
            await ctx.message.add_reaction("✅")
