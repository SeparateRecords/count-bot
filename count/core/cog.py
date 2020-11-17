from __future__ import annotations
from typing import Callable

import discord.ext.commands as commands
from loguru import logger

from count.errors import fail


def qualified_name(name: str) -> str:
    # if it's dotted, it's already qualified. assume it's fully qualified.
    if "." in name:
        return name
    return f"count.{name}"


class CoreCommands(commands.Cog, name="Bot"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._old_help = bot.help_command
        bot.help_command = commands.DefaultHelpCommand()
        bot.help_command.cog = self

    def cog_unload(self) -> None:
        self.bot.help_command = self._old_help

    @commands.command()
    @commands.is_owner()
    async def kys(self, ctx: commands.Context) -> None:
        """Kill the bot"""
        await ctx.message.add_reaction("💀")
        await ctx.bot.logout()
        logger.success("Bot has been closed.")

    @commands.command()
    @commands.is_owner()
    async def disconnect(self, ctx: commands.Context) -> None:
        """Disconnect from the current VC"""
        vc = ctx.voice_client
        if not vc:
            fail("No voice client is available.")
        try:
            vc.disconnect(force=True)
        except Exception as e:
            fail("Error during disconnect.", cause=e)

    @commands.group()
    @commands.is_owner()
    async def ext(self, ctx: commands.Context) -> None:
        """Interface with bot extensions directly"""
        if not ctx.subcommand_passed:
            await ctx.send_help(self.ext)

    @ext.command(name="load")
    async def ext_load(self, ctx: commands.Context, extension: str) -> None:
        """Load an extension"""
        await self.ext_subcommand_impl(
            ctx,
            ctx.bot.load_extension,
            qualified_name(extension),
        )

    @ext.command(name="reload")
    async def ext_reload(self, ctx: commands.Context, extension: str) -> None:
        """Reload an extension"""
        await self.ext_subcommand_impl(
            ctx,
            ctx.bot.reload_extension,
            qualified_name(extension),
        )

    @ext.command(name="unload")
    async def ext_unload(self, ctx: commands.Context, extension: str) -> None:
        """Unload an extension"""
        fqn = qualified_name(extension)
        if fqn == "count.core":
            logger.error("Cannot reload 'count.core' extension.")
            fail("The core extension can't be unloaded.")

        await self.ext_subcommand_impl(
            ctx,
            ctx.bot.unload_extension,
            extension,
        )

    async def ext_subcommand_impl(
        self,
        ctx: commands.Context,
        method: Callable[[str], None],
        ext: str,
    ) -> None:
        try:
            method(ext)
        except commands.ExtensionNotFound:
            fail(f"Unable to find extension: '{ext}'")
        except commands.ExtensionAlreadyLoaded:
            fail(f"Extension is already loaded: '{ext}'")
        except commands.ExtensionNotLoaded:
            fail(f"Extension is not loaded: '{ext}'")
        except commands.ExtensionFailed as err:
            fail(f"An exception occurred during setup/teardown,", cause=err)
        else:
            logger.success(f"(un/re)loaded extension successfully: {ext}")
            await ctx.message.add_reaction("✅")
