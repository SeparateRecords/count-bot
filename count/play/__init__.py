from __future__ import annotations

from pathlib import Path

import discord.ext.commands as commands

from count import config
from count.common import ConfigKey
from count.play.audio import config_to_assets
from count.play.cog import create_play_cog

COG_NAME = "Play"


def setup(bot: commands.Bot) -> None:
    path = config.get(bot, ConfigKey.AUDIO_CONFIG_PATH)

    if isinstance(path, Path):
        assets = config_to_assets(path)
        cog = create_play_cog(COG_NAME, assets)
        bot.add_cog(cog)
    else:
        raise ValueError("")


def teardown(bot: commands.Bot) -> None:
    bot.remove_cog(COG_NAME)
