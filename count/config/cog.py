from __future__ import annotations

from typing import Dict, Optional, TypeVar, Type

import discord.ext.commands as commands

Cls = TypeVar("Cls")


class ConfigCog(commands.Cog, name="<CONFIG>"):
    def __init__(self, bot: commands.Bot, data: Optional[Dict[object, object]]) -> None:
        self.bot = bot
        self.data = data or {}

    @classmethod
    def get_instance(cls: Type[Cls], bot: commands.Bot) -> Optional[Cls]:
        name = cls.__cog_name__  # type: ignore
        # get_cog returns commands.Cog because it doesn't know the type
        # of each cog. This is *almost* guaranteed safe.
        return bot.get_cog(name)  # type: ignore
