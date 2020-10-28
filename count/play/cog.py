from __future__ import annotations

import asyncio
import io
from typing import TYPE_CHECKING, cast

import discord
import discord.ext.commands as commands
from loguru import logger

from count.errors import fail
from count.play.audio import Countdown

if TYPE_CHECKING:
    from count.play.assets import PlayCogCommandStructure


def create_play_cog(name: str, all_assets: PlayCogCommandStructure) -> commands.Cog:
    """Generate a new cog containing commands that play audio."""
    countdown = Countdown(all_assets)

    cog_dict = {}
    for command_name, data in all_assets.items():
        max_countdown = max(data.keys())
        command = create_play_cog_command(command_name, countdown, max_countdown)
        cog_dict[command_name] = command

    NewCog = type(name, (commands.Cog,), cog_dict)
    cog_instance = NewCog()
    return cog_instance


def create_play_cog_command(
    command_name: str,
    countdown: Countdown,
    max_countdown: int,
) -> commands.Command:
    """Get a command that plays audio.

    The first argument of the command is unused because when cogs are
    created each command has `self` injected as the first positional
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
            countdown,
            max_countdown,
        )

    return play


async def play_audio(
    ctx: commands.Context,
    seconds: int,
    command_name: str,
    countdown: Countdown,
    max_countdown: int,
) -> None:
    """Play audio in the message author's voice channel."""
    if seconds > max_countdown:
        logger.error("Number to count from was greater than the maximum allowed.")
        fail(f"Too long, use a number under {max_countdown}.")

    if seconds < 0:
        logger.error("Number was under 0, unable to count.")
        fail(f"Can't count down from numbers below 0, please use a positive number.")

    if ctx.voice_client:
        logger.error(f"Voice client already exists for guild: {ctx.guild!r}.")
        fail("Already counting in your server.")

    try:
        vc = await ctx.author.voice.channel.connect()  # type: ignore
        vc = cast(discord.VoiceClient, vc)
    except AttributeError:
        logger.error(f"User not in a voice channel: {ctx.author.id}")
        fail("You must be in a voice channel.")
    except discord.ClientException as e:
        logger.error(f"Failed to connect: {e}")
        fail("Failed to connect to your voice channel.", cause=e)

    try:
        audio_bytes = countdown(seconds, command_name)
    except KeyError as e:
        fail(f"Unable to create audio for '{command_name}'", cause=e)

    audio_reader = io.BytesIO(audio_bytes)
    audio = discord.PCMAudio(audio_reader)

    await asyncio.sleep(0.5)

    try:
        vc.play(audio)
    except Exception as e:
        await vc.disconnect()
        fail(f"Couldn't count down.", cause=e)

    await asyncio.sleep(seconds + 1)

    # Just in case the final file was longer than 1s, don't cut it off.
    while vc.is_playing():
        await asyncio.sleep(1)

    await vc.disconnect()
