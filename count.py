from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import click
import dotenv
import discord
import discord.ext.commands as commands

logging.basicConfig(level=logging.INFO)

dotenv.load_dotenv(verbose=True)

repo = Path(__file__).resolve().parent

CUSTOM = repo / "custom_audio"
DEFAULT = repo / "default_audio"
SEQUENCE = 5, 4, 3, 2, 1, 0


def first(iterable, check=bool, *, default=None):
    """Get the first item of the iterable where `check(item)` isn't falsy."""
    for item in iterable:
        if check(item):
            return item
    return default


def get_prefix(bot: commands.Bot, msg: discord.Message) -> list[str]:
    """Invoke with `count::`, a mention, or nothing if the topic mentions the bot."""
    prefixes = ["count::"]
    prefixes += commands.when_mentioned(bot, msg)

    # The channel (DM) has no topic? Pretend the topic is a mention.
    # The topic will be None if unset, not an empty string :/
    topic = getattr(msg.channel, "topic", bot.user.mention) or ""

    if bot.user.mention in topic:
        prefixes.append("")

    return prefixes


bot = commands.Bot(command_prefix=get_prefix)


@bot.event
async def on_ready():
    """Log useful bot information on startup."""
    logging.info(f"Bot is ready: {bot.user}")
    logging.info(f"Bot ID: . . . {bot.user.id}")
    logging.info(f"Owner ID: . . {bot.owner_id}")


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    """Ignore `CommandNotFound` if the command prefix is omitted."""
    # The prefix can only be omitted in specific channels, this is fine.
    if isinstance(error, commands.CommandNotFound) and not ctx.prefix:
        return
    raise error


@bot.before_invoke
async def log_command_usage(ctx: commands.Context):
    """Log each command used, along with the author and timestamp."""
    msg = f"{ctx.author} invoked '{ctx.message.content}' at {ctx.message.created_at}"

    if ctx.guild:
        guild = ctx.guild
        channel = ctx.channel
        msg += f" in #{channel} ({channel.id}) of '{guild}' ({guild.id})"
    else:
        msg += f" in a DM"

    logging.info(msg)


@bot.group(aliases=["count"], brief="Count down from 3.")
@commands.guild_only()
async def go(ctx: commands.Context):
    """Count down from 3 in your voice channel. Alias for 'go from 3'"""
    if not ctx.subcommand_passed:
        await go_from(ctx, 3)


@go.command(name="from", brief="Count down from a specific number.")
@commands.guild_only()
async def go_from(ctx: commands.Context, begin: int):
    """Count down from a specific number in your voice channel."""
    if ctx.voice_client is not None:
        return await ctx.send("I'm already counting, please wait until I'm done!")

    if begin not in SEQUENCE:
        numbers = ", ".join(map(str, sorted(SEQUENCE)))
        return await ctx.send(f"I can only count down from these numbers: {numbers}")

    try:
        vc: discord.VoiceClient = await ctx.author.voice.channel.connect()
    except (AttributeError, discord.ClientException):
        return await ctx.send("You must be in a voice channel I can join.")

    # First audio file can get cut off at the start without waiting.
    await asyncio.sleep(0.5)

    # From the final item (0), take all items from 'begin' steps left.
    for n in SEQUENCE[-1 - begin:]:

        # If the previous file is still playing, stop it and warn.
        if vc.is_playing():
            vc.stop()
            logging.warning(f"{n+1}.wav is over 1 second, playback stopped.")

        # 'path' will be None if the default is missing.
        wav = f"{n}.wav"
        path = first((CUSTOM/wav, DEFAULT/wav), lambda f: f.exists())

        # Audio plays in a separate thread, don't await it.
        audio = discord.FFmpegPCMAudio(str(path))
        vc.play(audio)

        await asyncio.sleep(1)

    # If the last file is over 1 second, sleep until it ends.
    while vc.is_playing():
        await asyncio.sleep(0.5)

    await vc.disconnect()


@bot.command(aliases=["die"], brief="Shut down the bot.")
@commands.is_owner()
async def kill(ctx: commands.Context):
    """Close the connection to Discord, clean up the event loop, and exit."""
    await ctx.send("Closing connection and event loop.")
    await bot.close()


@click.command()
@click.option("-t", "--token", metavar="TOKEN", envvar="COUNT_BOT_TOKEN")
@click.option("-o", "--owner", metavar="ID", type=int, envvar="COUNT_BOT_OWNER")
@click.pass_context
def cli(ctx: click.Context, token: str, owner: int):
    if not token:
        ctx.fail("Token required, but none set.\nUsage: -t|--token TOKEN")

    if not owner:
        ctx.fail("The bot must have an owner.\nUsage: -o|--owner ID")

    bot.owner_id = owner
    bot.run(token)


if __name__ == "__main__":
    cli()
