from __future__ import annotations

from typing import Dict, Optional, TypeVar, Type

import discord.ext.commands as commands

from count.common import cog_name

Cls = TypeVar("Cls")


class ConfigCog(commands.Cog, name="Config Storage"):
    def __init__(self, bot: commands.Bot, data: Optional[Dict[object, object]]) -> None:
        self.bot = bot
        self.data = data or {}

    @classmethod
    def get_instance(cls: Type[Cls], bot: commands.Bot) -> Optional[Cls]:
        # get_cog returns commands.Cog because it doesn't know the type
        # of each cog. This is *almost* guaranteed safe.
        return bot.get_cog(cog_name(cls))  # type: ignore
