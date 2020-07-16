import asyncio
import logging
from pathlib import Path
from typing import List

import click
import discord
import discord.ext.commands as commands
from dotenv import find_dotenv, load_dotenv

logging.basicConfig(level=logging.INFO)

load_dotenv(find_dotenv(), verbose=True)

repo = Path(__file__).resolve().parent
custom = repo / "custom_audio"
default = repo / "default_audio"


def first(iterable, check=bool, *, default=None):
    """Get the first item of the iterable where `check(item)` isn't falsy."""
    return next((item for item in iterable if check(item)), default)


def get_prefix(bot: commands.Bot, msg: discord.Message) -> List[str]:
    """Invoke with `count::`, a mention, or nothing if the topic mentions the bot."""
    prefixes = ["count::"]
    prefixes += commands.when_mentioned(bot, msg)

    mention = bot.user.mention
    topic = getattr(msg.channel, "topic", mention)

    if topic and mention in topic:
        prefixes.append("")

    return prefixes


client = commands.Bot(command_prefix=get_prefix)


@client.event
async def on_ready():
    """Log useful bot information on startup."""
    logging.info(f"Bot is ready: {client.user}")
    logging.info(f"Bot ID: . . . {client.user.id}")
    logging.info(f"Owner ID: . . {client.owner_id}")


@client.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    """Ignore `CommandNotFound` if the command prefix is omitted."""
    # The prefix can only be omitted in specific channels, this is fine.
    if isinstance(error, commands.CommandNotFound) and not ctx.prefix:
        return
    raise error


@client.before_invoke
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


@client.group(brief="Count down from 3.")
@commands.guild_only()
async def go(ctx: commands.Context):
    """Count down from 3 in your voice channel. Alias for 'go from 3'"""
    if not ctx.subcommand_passed:
        await go_from(ctx, 3)


@go.command(name="from", brief="Count down from a specific number.")
@commands.guild_only()
async def go_from(ctx: commands.Context, begin: int):
    """Count down from a number in your voice channel (max = 5, min = 0)"""
    if ctx.voice_client is not None:
        return await ctx.send("I'm already counting, please wait until I'm done!")

    if begin not in range(6):
        return await ctx.send("I can only count down using numbers between 0 and 5 :(")

    try:
        vc: discord.VoiceClient = await ctx.author.voice.channel.connect()
    except (AttributeError, discord.ClientException):
        return await ctx.send("You must be in a voice channel I can join.")

    # First audio file can get cut off at the start without waiting.
    await asyncio.sleep(0.5)

    # The stop param is non-inclusive, offset by 1.
    for n in reversed(range(begin + 1)):

        # If the previous file is still playing, stop it and warn.
        if vc.is_playing():
            vc.stop()
            logging.warning(f"{n+1}.wav is over 1 second, playback stopped.")

        # 'path' will be None if the default is missing.
        wav = f"{n}.wav"
        path = first((custom/wav, default/wav), lambda f: f.exists())

        # Audio plays in a separate thread, don't await it.
        audio = discord.FFmpegPCMAudio(str(path))
        vc.play(audio)

        await asyncio.sleep(1)

    # If the last file is over 1 second, sleep until it ends.
    while vc.is_playing():
        await asyncio.sleep(0.5)

    await vc.disconnect()


@client.command(aliases=["die"], brief="Shut down the bot.")
@commands.is_owner()
async def kill(ctx: commands.Context):
    """Close the connection to Discord, clean up the event loop, and exit."""
    await ctx.send("Closing connection and event loop.")
    await client.close()


@click.command()
@click.option("-t", "--token", metavar="TOKEN", envvar="COUNT_BOT_TOKEN")
@click.option("-o", "--owner", metavar="ID", type=int, envvar="COUNT_BOT_OWNER")
@click.pass_context
def cli(ctx: click.Context, token: str, owner: int):
    if not token:
        ctx.fail("Token required, but none set.\nUsage: -t|--token TOKEN")

    if not owner:
        ctx.fail("The bot must have an owner.\nUsage: -o|--owner ID")

    client.owner_id = owner
    client.run(token)


if __name__ == "__main__":
    cli()
