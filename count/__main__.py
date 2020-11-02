from __future__ import annotations

# fmt: off
__import__("dotenv").load_dotenv()
# fmt: on

import asyncio
import logging
import sys
from inspect import cleandoc
from pathlib import Path
from typing import Any, Optional, Sequence

import click
import discord
from loguru import logger

from count.bot import new_bot


class RedirectToLoguru(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            loguru_level = logger.level(record.levelname).name
        except ValueError:
            loguru_level = record.levelno

        frame = logging.currentframe()
        depth = 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            if not frame:
                break
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(  # type: ignore
            loguru_level, record.getMessage()
        )


logging.basicConfig(handlers=[RedirectToLoguru()], level=0)


if hasattr(discord.client, "_cleanup_loop"):
    # it's private so it may change at any time, worth checking ahead
    # of time so I can be alerted if it ever goes missing

    def _cleanup_loop(loop: asyncio.BaseEventLoop) -> None:
        try:
            discord.client._cancel_tasks(loop)  # type: ignore
            if sys.version_info >= (3, 6):
                loop.run_until_complete(loop.shutdown_asyncgens())
        finally:
            # wait a bit longer for aiohttp tasks to finish to avoid
            # the incredibly ugly (but ultimately harmless) exception
            loop.run_until_complete(asyncio.sleep(1))
            loop.close()

    setattr(discord.client, "_cleanup_loop", _cleanup_loop)

else:
    msg = "discord.client._cleanup_loop doesn't exist, shutdown may not be graceful"
    logger.warning(msg)


class PathPath(click.Path):
    def convert(
        self,
        value: str,
        param: Optional[click.Parameter],
        ctx: Optional[click.Context],
    ) -> Any:
        return Path(super().convert(value, param, ctx))


@click.command()
@click.option(
    "--token",
    "-t",
    help="The token to use when logging in.",
    required=True,
    metavar="<token>",
    envvar="COUNT_BOT_TOKEN",
    prompt="Bot token",
)
@click.option(
    "--owner",
    "-o",
    "owners",
    help=(
        "If given, overrides the owner(s) of the bot. "
        "Allows multiple owners by using this option once per ID."
    ),
    metavar="<id>",
    envvar="COUNT_BOT_OWNERS",
    multiple=True,
    type=int,
)
@click.option(
    "--override-config",
    "-c",
    "config",
    help="Specify a custom config INI file.",
    metavar="<path>",
    envvar="COUNT_BOT_CUSTOM_CONFIG",
    default=Path(__file__).resolve().parent / "assets/config.ini",
    type=PathPath(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
        allow_dash=False,
    ),
)
@click.option(
    "--prefix",
    "-p",
    "prefix",
    help="Set the prefix used to invoke commands.",
    metavar="<str>",
    envvar="COUNT_BOT_PREFIX",
    default=".",
    show_default=True,
)
@click.option(
    "--log-level",
    help="Log level of the bot.",
    metavar="<level>",
    envvar="COUNT_BOT_LOG_LEVEL",
    default="INFO",
    show_default=True,
    type=click.Choice(
        ["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"],
        case_sensitive=True,
    ),
)
@click.option(
    "--dpy-log-level",
    help="Log level of discord.py.",
    metavar="<level>",
    envvar="COUNT_BOT_DISCORD_LOG_LEVEL",
    default="ERROR",
    show_default=True,
    type=click.Choice(
        ["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"],
        case_sensitive=True,
    ),
)
@click.pass_context
def cli(
    ctx: click.Context,
    token: str,
    owners: Sequence[int],
    config: Path,
    prefix: str,
    log_level: str,
    dpy_log_level: str,
):
    """
    Run the bot using constants provided through environment variables
    or the CLI.

    Once the bot is running, these values will not change.
    """
    logger.remove()
    logger.add(
        sys.stderr,
        filter="discord",
        level=dpy_log_level,
    )
    show_debug_info = logger.level(log_level).no < logger.level("INFO").no
    logger.add(
        sys.stderr,
        filter="count",
        level=log_level,
        backtrace=show_debug_info,
        diagnose=show_debug_info,
    )

    bot = new_bot(prefix, owners, config)
    try:
        bot.run(token)
    except discord.PrivilegedIntentsRequired:
        msg = cleandoc(
            """
            count-bot needs the 'members' intent, which must be enabled
            in the developer portal of your bot. It isn't technically
            required, but omitting it can trigger weird errors because
            discord.py makes certain assumptions about the member cache
            that may not be true without it.
            """
        )
        ctx.fail(msg)


if __name__ == "__main__":
    cli()
