from __future__ import annotations

import copy
from typing import Dict, Optional, TypeVar

import discord.ext.commands as commands

from count.config.cog import ConfigCog

T = TypeVar("T")


def install(
    bot: commands.Bot,
    initial_config: Optional[Dict[object, object]] = None,
) -> None:
    if ConfigCog.get_instance(bot):
        return None
    # The only way to modify data should be be through the get/set
    # functions.
    data = copy.deepcopy(initial_config)
    bot.add_cog(ConfigCog(bot, data))


def get(bot: commands.Bot, key: object, default: object = None) -> Optional[object]:
    conf = ConfigCog.get_instance(bot)
    if not conf:
        return None
    return conf.data.get(key)


def set(bot: commands.Bot, key: object, value: T) -> Optional[T]:
    conf = ConfigCog.get_instance(bot)
    if not conf:
        return None
    conf.data[key] = value
    return value


def setdefault(bot: commands.Bot, key: object, value: T) -> Optional[T]:
    conf = ConfigCog.get_instance(bot)
    if not conf:
        return None
    return conf.data.setdefault(key, value)
