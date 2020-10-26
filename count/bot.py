from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Collection

import discord
import discord.ext.commands as commands
from loguru import logger

from count import config
from count.common import ConfigKey
from count.errors import ShowFailureInChat

if TYPE_CHECKING:
    from pathlib import Path


class Bot(commands.Bot):
    async def close(self) -> None:
        await asyncio.gather(
            *[vc.disconnect(force=True) for vc in self.voice_clients],
            self.change_presence(status=discord.Status.offline),
        )
        await super().close()

    async def on_ready(self) -> None:
        logger.info("Bot is ready.")

    async def on_command_error(
        self,
        ctx: commands.Context,
        exception: BaseException,
    ) -> None:
        if isinstance(exception, ShowFailureInChat):
            await ctx.send(exception)
            # The cause should be raised as its own error, ShowFailure
            # just wraps it to show some useful information to the user.
            if not exception.__cause__:
                return

            # Not returning, this will be logged.
            exception = exception.__cause__

        elif isinstance(exception, commands.MissingRequiredArgument):
            await ctx.send_help(ctx.invoked_subcommand)
            return

        # If there's no specific handling, the error should not be silent.
        logger.opt(exception=exception).error("Something has gone terribly wrong.")


async def log_command_usage(ctx: commands.Context) -> None:
    msg = f"{ctx.author} sent '{ctx.message.content}'"

    if ctx.guild:
        guild = ctx.guild
        channel = ctx.channel
        msg += f" in '{guild}' ({guild.id}), #{channel} ({channel.id})"
    else:
        msg += f" in a DM"

    logger.info(msg)


@logger.catch
def new_bot(prefix: str, owners: Collection[int], audio_config_path: Path) -> Bot:
    """Create a new bot instance with cogs loaded."""

    # the member cache is extremely flaky without the 'members' intent.
    bot = Bot(
        command_prefix=prefix,
        case_insensitive=True,
        owner_ids=set(owners),
        description="Counts down for you, so you have an easier time staying in sync.",
        intents=discord.Intents(**dict(discord.Intents.default(), members=True)),
    )

    bot.before_invoke(log_command_usage)

    initial_config = {
        ConfigKey.AUDIO_CONFIG_PATH: audio_config_path,
    }
    config.install(bot, initial_config)

    bot.load_extension("count.core")
    bot.load_extension("count.play")

    return bot
