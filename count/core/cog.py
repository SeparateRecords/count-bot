from __future__ import annotations
from typing import Callable

import discord.ext.commands as commands
from loguru import logger

from count.errors import fail


class CoreCommands(commands.Cog, name="Bot"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._old_help = bot.help_command
        bot.help_command = commands.DefaultHelpCommand()
        bot.help_command.cog = self

    def cog_unload(self) -> None:
        self.bot.help_command = self._old_help

    async def cog_check(self, ctx: commands.Context) -> bool:
        return await ctx.bot.is_owner(ctx.author)

    @commands.command()
    async def kys(self, ctx: commands.Context) -> None:
        """Stop the bot."""
        await ctx.message.add_reaction("💀")
        await ctx.bot.logout()
        logger.success("Bot has been closed.")

    async def ext_re_un_load(
        self,
        ctx: commands.Context,
        ext: str,
        method: Callable[[str], None],
    ) -> None:
        # If it's qualified, treat it as literal, otherwise local.
        fqn = ext if "." in ext else f"count.{ext}"
        try:
            method(fqn)
        except commands.ExtensionNotFound:
            fail(f"Unable to find extension: '{fqn}'")
        except commands.ExtensionAlreadyLoaded:
            fail(f"Extension is already loaded: '{fqn}'")
        except commands.ExtensionNotLoaded:
            fail(f"Extension is not loaded: '{fqn}'")
        except commands.ExtensionFailed as err:
            fail(f"An exception was raised by the extension.", cause=err)
        else:
            logger.success(f"(un/re)loaded extension successfully: {fqn}")
            await ctx.message.add_reaction("✅")

    @commands.group()
    async def ext(self, ctx: commands.Context) -> None:
        """Interface with bot extensions directly."""
        if not ctx.subcommand_passed:
            await ctx.send_help(self.ext)

    @ext.command(name="load")
    async def ext_load(self, ctx: commands.Context, extension: str) -> None:
        """Load an extension."""
        await self.ext_re_un_load(ctx, extension, ctx.bot.load_extension)

    @ext.command(name="reload")
    async def ext_reload(self, ctx: commands.Context, extension: str) -> None:
        """Reload an extension."""
        await self.ext_re_un_load(ctx, extension, ctx.bot.reload_extension)

    @ext.command(name="unload")
    async def ext_load(self, ctx: commands.Context, extension: str) -> None:
        """Unload an extension."""
        await self.ext_re_un_load(ctx, extension, ctx.bot.unload_extension)
