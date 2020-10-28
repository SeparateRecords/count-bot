from __future__ import annotations

from copy import deepcopy as copy
from typing import Dict, Optional, TypeVar

import discord.ext.commands as commands

from count.config.cog import ConfigCog

T = TypeVar("T")


def install(
    bot: commands.Bot,
    initial_config: Optional[Dict[object, object]] = None,
) -> None:
    """Install the configuration storage on the bot."""
    if ConfigCog.get_instance(bot):
        return None
    # The only way to modify data should be be through the get/set
    # functions.
    if initial_config is not None:
        data = copy(initial_config)
    else:
        data = {}
    bot.add_cog(ConfigCog(bot, data))


def get(bot: commands.Bot, key: object, default: object = None) -> Optional[object]:
    """Get a copy of data stored in the bot."""
    conf = ConfigCog.get_instance(bot)
    if not conf:
        return None
    return copy(conf.data.get(key, default))


def set(bot: commands.Bot, key: object, value: T) -> bool:
    """Set a key in the bot storage to a copy of the data.

    Returns True if the value was set successfully.
    """
    conf = ConfigCog.get_instance(bot)
    if not conf:
        return False
    conf.data[key] = copy(value)
    return True
