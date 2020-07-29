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
SEQUENCE = 5, 4, 3, 2, 1
GO = "go.wav"
PAUSE = "pause.wav"


def get_audio(wav: str) -> discord.FFmpegPCMAudio:
    """Get the file named `name` from the user's custom files, or the default."""
    path = CUSTOM / wav

    if not path.exists():
        path = DEFAULT / wav

    return discord.FFmpegPCMAudio(path)


bot = commands.Bot(command_prefix=".")


@bot.group(brief="Say 'Go' after 3 seconds.")
@commands.guild_only()
async def go(ctx: commands.Context):
    """Count down from 3 in your voice channel. Alias for 'go in 3'"""
    if not ctx.subcommand_passed:
        await countdown(ctx, 3, on_zero=GO)


@go.command(name="in", brief="Say 'Go' after a given number of seconds.")
@commands.guild_only()
async def go_in(ctx: commands.Context, seconds: int):
    """Join your voice channel and say 'Go' after a given number of seconds."""
    await countdown(ctx, seconds, on_zero=GO)


@bot.group(aliases=["stop"], brief="Say 'Pause' after 3 seconds.")
@commands.guild_only()
async def pause(ctx: commands.Context):
    """Count down from 3 in your voice channel. Alias for 'pause in 3'"""
    if not ctx.subcommand_passed:
        await countdown(ctx, 3, on_zero=PAUSE)


@pause.command(name="in", brief="Say 'Pause' after a given number of seconds.")
@commands.guild_only()
async def pause_in(ctx: commands.Context, seconds: int):
    """Join your voice channel and say 'Pause' after a given number of seconds."""
    await countdown(ctx, seconds, on_zero=PAUSE)


async def countdown(ctx: commands.Context, seconds: int, *, on_zero: str):
    """Begin counting down from `seconds`, then play `on_zero`."""
    if ctx.voice_client is not None:
        return await ctx.send("I'm already counting, please wait until I'm done!")

    if seconds not in SEQUENCE:
        msg = f"Use a number between {max(SEQUENCE)} and {min(SEQUENCE)}."
        return await ctx.send(msg)

    try:
        vc: discord.VoiceClient = await ctx.author.voice.channel.connect()
    except (AttributeError, discord.ClientException):
        return await ctx.send("You must be in a voice channel I can join.")

    # Turns out audio can get cut off at the start if you don't wait.
    await asyncio.sleep(0.5)

    for n in SEQUENCE[-seconds:]:
        audio = get_audio(f"{n}.wav")
        vc.play(audio)

        await asyncio.sleep(1)

        # Previous file could still be playing if over 1 second.
        if vc.is_playing():
            vc.stop()

    audio = get_audio(on_zero)
    vc.play(audio)

    # If the last file is over 1 second, sleep until it ends.
    while vc.is_playing():
        await asyncio.sleep(1)

    await vc.disconnect()


@bot.command(brief="Shut down the bot.", hidden=True)
@commands.is_owner()
async def kys(ctx: commands.Context):
    """Close the connection to Discord, clean up the event loop, and exit."""
    await ctx.message.add_reaction("💀")
    await bot.close()


@bot.event
async def on_ready():
    """Log useful bot information on startup."""
    logging.info(f"Bot is ready: {bot.user}")
    logging.info(f"Bot ID: . . . {bot.user.id}")
    logging.info(f"Owner ID: . . {bot.owner_id}")


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


@click.command()
@click.option("-t", "--token", required=True, metavar="TOKEN", envvar="COUNT_BOT_TOKEN")
@click.option("-o", "--owner", required=True, metavar="ID", type=int, envvar="COUNT_BOT_OWNER")
def cli(token: str, owner: int):
    bot.owner_id = owner
    bot.run(token)


if __name__ == "__main__":
    cli()
