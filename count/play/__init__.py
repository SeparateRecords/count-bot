from __future__ import annotations

from pathlib import Path
from typing import cast

from discord.ext import commands

from count import config
from count.common import ConfigKey, cog_name
from count.play.cog import AudioManager


def setup(bot: commands.Bot) -> None:
    path = config.get(bot, ConfigKey.AUDIO_CONFIG_PATH)
    assert path  # no reason it shouldn't exist, but just in case.
    bot.add_cog(AudioManager(bot, cast(Path, path)))


def teardown(bot: commands.Bot) -> None:
    bot.remove_cog(cog_name(AudioManager))
