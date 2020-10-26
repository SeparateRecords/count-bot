from __future__ import annotations

from enum import Enum, auto
from typing import Type, Union

import discord.ext.commands as commands


class ConfigKey(Enum):
    AUDIO_CONFIG_PATH = auto()


def cog_name(cog: Union[Type[commands.Cog], commands.Cog]) -> str:
    return cog.__cog_name__  # type: ignore
