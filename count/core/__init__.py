from __future__ import annotations

import discord.ext.commands as commands

from count.core.cog import CoreCommands


def setup(bot: commands.Bot) -> None:
    bot.add_cog(CoreCommands(bot))


def teardown(bot: commands.Bot) -> None:
    bot.remove_cog(CoreCommands.__cog_commands__)
