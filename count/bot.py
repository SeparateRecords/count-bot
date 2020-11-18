from __future__ import annotations

from typing import TYPE_CHECKING, Any, Collection

import discord
import discord.ext.commands as commands
from loguru import logger

from count import bot_state
from count.errors import ShowFailureInChat

if TYPE_CHECKING:
    from pathlib import Path


class Bot(commands.Bot):
    async def on_ready(self) -> None:
        logger.info("Bot is ready.")

    async def on_error(self, event_method: str, *args: Any, **kwargs: Any) -> None:
        logger.exception(f"Ignoring exception in '{event_method}':")

    async def on_command_error(
        self,
        context: commands.Context,
        exception: BaseException,
    ) -> None:
        # ShowFailureInChat will send a message to a context, optionally
        # wrapping another error which should be handled separately.
        if isinstance(exception, ShowFailureInChat):
            await context.send(exception)

            # Was just used to send a message, don't log anything.
            if not exception.__cause__:
                return

            exception = exception.__cause__

            # If it wasn't wrapping a CommandError, log it and return.
            if not isinstance(exception, commands.CommandError):
                logger.opt(exception=exception).error("fail() wrapped")
                return

        if isinstance(exception, commands.MissingRequiredArgument):
            command = context.invoked_subcommand or context.command
            await context.send_help(command)
            return

        elif isinstance(exception, commands.CommandNotFound):
            return

        # If there's no specific handling, the error should not be silent.
        logger.opt(exception=exception).error("Ignoring CommandError:")


async def log_command_usage(ctx: commands.Context) -> None:
    msg = f"{ctx.author} sent '{ctx.message.content}'"

    if ctx.guild:
        msg += f" in '{ctx.guild}' #{ctx.channel}"
    else:
        msg += f" in a DM"

    logger.info(msg)


@logger.catch
def create_bot(prefix: str, owners: Collection[int], audio_config_path: Path) -> Bot:
    """Create a new bot instance with cogs loaded."""

    bot = Bot(
        command_prefix=prefix,
        case_insensitive=True,
        owner_ids=set(owners),
        description="Counts down for you, so you have an easier time staying in sync.",
        # member cache is extremely flaky without the 'members' intent
        intents=discord.Intents(**dict(discord.Intents.default(), members=True)),
    )

    bot.before_invoke(log_command_usage)

    initial_config = {"AUDIO_CONFIG_PATH": audio_config_path}
    bot_state.setup(bot, initial_config)

    bot.load_extension("count.core")
    bot.load_extension("count.play")

    return bot
