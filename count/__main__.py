from __future__ import annotations

# fmt: off
__import__("dotenv").load_dotenv()
# fmt: on

import logging
import sys
from pathlib import Path
from typing import Sequence

import click
from loguru import logger

from count.bot import new_bot


class RedirectToLoguru(logging.Handler):
    def emit(self, record):
        try:
            loguru_level = logger.level(record.levelname).name
        except ValueError:
            loguru_level = record.levelno

        frame = logging.currentframe()
        depth = 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            loguru_level, record.getMessage()
        )


logging.basicConfig(handlers=[RedirectToLoguru()], level=0)


class PathPath(click.Path):
    def convert(self, value, param, ctx):
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
def cli(
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
        enqueue=True,
    )
    show_debug_info = logger.level(log_level).no < logger.level("INFO").no
    logger.add(
        sys.stderr,
        filter="count",
        level=log_level,
        backtrace=show_debug_info,
        diagnose=show_debug_info,
        enqueue=True,
    )

    bot = new_bot(prefix, owners, config)
    bot.run(token)


if __name__ == "__main__":
    cli()
