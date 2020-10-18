from __future__ import annotations

import asyncio
import io
from typing import TYPE_CHECKING

import discord
import discord.ext.commands as commands
from loguru import logger

from count.countdown.audio import CountAudio
from count.errors import fail

if TYPE_CHECKING:
    from count.countdown.assets import AllAssets

COG_NAME = "Play"


def create_commands_cog(all_assets: AllAssets) -> commands.Cog:
    """Generate a new cog containing commands that play audio."""
    audio = CountAudio(all_assets)

    cog_dict = {}
    for command_name, data in all_assets.items():
        max_countdown = max(data.keys())
        command = create_cog_command(command_name, audio, max_countdown)
        cog_dict[command_name] = command

    NewCog = type(COG_NAME, (commands.Cog,), cog_dict)
    cog = NewCog()
    return cog


def create_cog_command(
    command_name: str,
    count_audio: CountAudio,
    max_countdown: int,
) -> commands.Command:
    """Get a command that plays audio.

    The first argument of the command is unused because when cogs are
    created the commands have `self` injected as the first positional
    argument.

    Command objects returned by this function are basically shims for
    `play_audio`.
    """
    default = min(3, max_countdown)

    @commands.command(name=command_name)
    @commands.guild_only()
    async def play(_, ctx: commands.Context, seconds: int = default) -> None:
        await play_audio(
            ctx,
            seconds,
            command_name,
            count_audio,
            max_countdown,
        )

    return play


async def play_audio(
    ctx: commands.Context,
    seconds: int,
    command_name: str,
    count_audio: CountAudio,
    max_countdown: int,
) -> None:
    """Play audio in the message author's voice channel."""
    if seconds > max_countdown:
        logger.error(f"Number to count from was greater than the maximum allowed.")
        fail(f"Too long, use a number under {max_countdown}.")

    if ctx.voice_client is not None:
        logger.error(f"Voice client already exists for guild: {ctx.guild.id}.")
        fail("Already counting in your server.")

    try:
        vc = await ctx.author.voice.channel.connect()  # type: ignore
    except AttributeError:
        logger.error(f"User not in a voice channel: {ctx.author.id}")
        fail("You must be in a voice channel.")
    except discord.ClientException as e:
        logger.error(f"Failed to connect: {e}")
        fail("Failed to connect to your voice channel.", cause=e)

    try:
        audio_bytes = count_audio.new(seconds, command_name)
    except KeyError as e:
        fail("Something has gone terribly wrong (unable to play)", cause=e)

    audio_io = io.BytesIO(audio_bytes)
    audio = discord.PCMAudio(audio_io)

    await asyncio.sleep(0.5)

    try:
        vc.play(audio)
    except Exception as e:
        await vc.disconnect()
        fail(f"Failed to play: {e}", cause=e)

    await asyncio.sleep(seconds + 1)

    # Just in case the final file was longer than 1s, don't cut it off.
    while vc.is_playing():
        await asyncio.sleep(1)

    await vc.disconnect()
