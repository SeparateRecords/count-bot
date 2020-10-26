from __future__ import annotations

import discord.ext.commands as commands

from count.core.cog import CoreCommands
from count.common import cog_name


def setup(bot: commands.Bot) -> None:
    bot.add_cog(CoreCommands(bot))


def teardown(bot: commands.Bot) -> None:
    bot.remove_cog(cog_name(CoreCommands))
