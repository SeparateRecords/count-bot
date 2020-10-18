"""
This file is only used to separate the bot definition from any
information required at runtime. Any and all useful information is in
__init__.py.
"""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Awaitable, Set

import discord
import discord.ext.commands as commands
from loguru import logger

from count.countdown import CountdownManagement
from count.errors import ShowFailureInChat

if TYPE_CHECKING:
    from pathlib import Path


class Bot(commands.Bot):
    async def close(self):
        await asyncio.gather(
            *[vc.disconnect(force=True) for vc in self.voice_clients],
            self.change_presence(status=discord.Status.offline),
        )
        await asyncio.sleep(1)
        await super().close()

    async def on_ready(self):
        logger.info("Bot is ready.")

    async def on_command_error(
        self,
        ctx: commands.Context,
        exception: Exception,
    ) -> None:
        if isinstance(exception, ShowFailureInChat):
            await ctx.send(embed=exception.embed())
            # The cause should be raised as its own error, ShowFailure
            # just wraps it to show some useful information to the user.
            if exception.__cause__:
                raise exception.__cause__
            return

        # If there's no specific handling, the error should not be silent.
        raise exception


class OwnerCommands(commands.Cog, name="Owner-only commands"):
    async def cog_check(self, ctx: commands.Context) -> bool:
        return await ctx.bot.is_owner(ctx.author)

    @commands.command()
    async def kys(self, ctx: commands.Context) -> None:
        await ctx.message.add_reaction("💀")
        await ctx.bot.logout()
        logger.success("Bot has been closed.")


async def log_commands(ctx: commands.Context) -> None:
    msg = f"{ctx.author} invoked '{ctx.message.content}' at {ctx.message.created_at}"

    if ctx.guild:
        guild = ctx.guild
        channel = ctx.channel
        msg += f" in #{channel} ({channel.id}) of '{guild}' ({guild.id})"
    else:
        msg += f" in a DM"

    logger.info(msg)


def new_bot(prefix: str, owners: Set[int], config: Path) -> Bot:

    # --- Create the bot ---

    intents = discord.Intents.default()
    intents.members = True
    bot = Bot(
        command_prefix=prefix,
        case_insensitive=True,
        description="Counts down for you, so you have an easier time staying in sync.",
        intents=intents,
    )
    bot.owner_ids = owners
    bot.before_invoke(log_commands)

    # --- Create the countdown commands ---

    countdown = CountdownManagement(bot, config)
    bot.add_cog(countdown)

    # --- Add commands for bot control ---

    bot.add_cog(OwnerCommands())

    return bot
