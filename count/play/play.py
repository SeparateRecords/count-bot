from __future__ import annotations

import asyncio
import io
from typing import Any, Dict, Iterator, Optional, Sequence, cast, Protocol

import discord
import discord.ext.commands as commands
from loguru import logger

from count.errors import fail
from count.play.audio import Counter
from count.play.config import CommandConfigData


class CommandFactory(Protocol):
    def __call__(
        self, name: str, data: CommandConfigData, counter: Counter
    ) -> Optional[commands.Command]:
        ...


def create_play_cog(cog_name: str, assets: CommandConfigData) -> commands.Cog:
    """Generate a new cog containing commands that play audio."""
    cog_dict: Dict[str, Any] = {}
    counter = Counter(assets)

    def name_gen() -> Iterator[str]:
        i = 0
        while True:
            i += 1
            yield f"__{i}"

    cmd_names = name_gen()

    for name, data in assets.items():

        cog_dict[next(cmd_names)] = new_command(
            command_name=name,
            asset_name=name,
            aliases=data["metadata"]["aliases"],
            count=counter,
            max_countdown=max(data["audio"].keys()),
        )

    NewCog = type(cog_name, (commands.Cog,), cog_dict)
    return NewCog()


def new_command(
    command_name: str,
    asset_name: str,
    aliases: Sequence[str],
    count: Counter,
    max_countdown: int,
) -> commands.Command:
    default = 3

    @commands.command(name=command_name, aliases=list(aliases))
    @commands.guild_only()
    async def play(_, ctx: commands.Context, seconds: int = default) -> None:

        if seconds > max_countdown:
            logger.error("Number to count from was greater than the maximum allowed.")
            fail(f"Too long, use a number under {max_countdown}.")

        if seconds < 0:
            logger.error("Number was under 0, unable to count.")
            fail(
                f"Can't count down from numbers below 0, please use a positive number."
            )

        vc = await join_author_vc(ctx)

        try:
            audio = count(seconds, asset_name)
        except KeyError as e:
            fail(f"Unable to create audio for '{asset_name}'", cause=e)

        stream = io.BytesIO(audio)
        source = discord.PCMAudio(stream)
        vc.play(source)

        while vc.is_playing():
            await asyncio.sleep(1)

        await vc.disconnect()

    return play


async def join_author_vc(ctx: commands.Context) -> discord.VoiceClient:
    author = ctx.author

    if not isinstance(author, discord.Member):
        raise Exception("context.author is not a discord.Member")

    voice_state = author.voice

    if not voice_state:
        logger.error

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

    return vc
