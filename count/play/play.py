from __future__ import annotations

import asyncio
import io
from typing import Any, Dict, Iterator, List, cast

import discord
import discord.ext.commands as commands
from loguru import logger

from count.errors import fail
from count.play.audio import Counter
from count.play.config import PlayCogCommandStructure


def create_play_cog(cog_name: str, assets: PlayCogCommandStructure) -> commands.Cog:
    """Generate a new cog containing commands that play audio."""
    cog_dict: Dict[str, Any] = {}
    count = Counter(assets)

    def name_gen() -> Iterator[str]:
        i = 0
        while True:
            i += 1
            yield f"__{i}"

    cmd_names = name_gen()

    for command_name, data in assets.items():
        max_countdown = max(data["audio"].keys())
        aliases = data["metadata"]["aliases"]

        cog_dict[next(cmd_names)] = new_command(
            command_name,
            command_name,
            aliases,
            count,
            max_countdown,
        )

    NewCog = type(cog_name, (commands.Cog,), cog_dict)
    return NewCog()


def new_command(
    command_name: str,
    asset_name: str,
    aliases: List[str],
    count: Counter,
    max_countdown: int,
) -> commands.Command:
    """Get a command that plays audio. Basically a shim for `play_audio`"""

    default = min(3, max_countdown)

    # The first argument of the command is unused because when cogs are
    # created each command has `self` injected as the first positional
    # argument.

    @commands.command(name=command_name, aliases=aliases)
    @commands.guild_only()
    async def play(_, ctx: commands.Context, seconds: int = default) -> None:
        await play_audio(
            ctx,
            seconds,
            asset_name,
            count,
            default,
        )

    return play


async def play_audio(
    ctx: commands.Context,
    seconds: int,
    asset_key: str,
    count: Counter,
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
        # if it's not a VoiceClient, then it raised an exception.
        vc = await ctx.author.voice.channel.connect()  # type: ignore
        vc = cast(discord.VoiceClient, vc)
    except AttributeError:
        logger.error(f"User not in a voice channel: {ctx.author.id}")
        fail("You must be in a voice channel.")
    except discord.ClientException as e:
        logger.error(f"Failed to connect: {e}")
        fail("Failed to connect to your voice channel.", cause=e)

    try:
        audio_bytes = count(seconds, asset_key)
    except KeyError as e:
        fail(f"Unable to create audio for '{asset_key}'", cause=e)

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
