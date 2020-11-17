from __future__ import annotations

from pathlib import Path

import discord.ext.commands as commands

from count import config
from count.play.config import create_assets
from count.play.play import create_play_cog


def setup(bot: commands.Bot) -> None:
    path = config.get(bot, "AUDIO_CONFIG_PATH")

    if not isinstance(path, Path):
        raise ValueError(f"AUDIO_CONFIG_PATH must be a pathlib.Path, was {type(path)}")

    # Any commands that currently exist can't be used as names for play commands
    illegal_command_names = [cmd.name for cmd in bot.commands]

    assets = create_assets(path, illegal_command_names)

    play = create_play_cog("Play", assets)
    bot.add_cog(play)


def teardown(bot: commands.Bot) -> None:
    bot.remove_cog("Play")
    bot.remove_cog("Prompt")
