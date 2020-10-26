from __future__ import annotations

import asyncio
import io
from pathlib import Path
from typing import TYPE_CHECKING, cast

import discord
import discord.ext.commands as commands
from loguru import logger

from count.errors import fail
from count.play.assets import config_to_assets
from count.play.audio_creator import AudioCreator

if TYPE_CHECKING:
    from count.play.assets import PlayCogCommandStructure

COG_NAME = "Play"


class AudioManager(commands.Cog, name="Audio"):
    """Manage the dynamically generated commands for counting."""

    def __init__(
        self,
        bot: commands.Bot,
        config_path: Path,
    ) -> None:
        self.bot = bot
        self.config_path = config_path
        self.add_commands_to_bot()

    def cog_unload(self):
        """Removes the generated cog when this cog is unloaded."""
        self.bot.remove_cog(COG_NAME)

    def add_commands_to_bot(self):
        """Generates the cog and registers it to the bot.

        If the cog is already loaded, it will be unloaded first.
        """
        # This goes first so that if it fails (for some reason)
        # then nothing will be changed.
        cog = self.create_cog()
        self.bot.remove_cog(COG_NAME)
        self.bot.add_cog(cog)

    def create_cog(self):
        """Creates the cog from the stored config."""
        assets = config_to_assets(self.config_path)
        cog = create_play_cog(assets)
        return cog

    @commands.command(hidden=True)
    @commands.is_owner()
    async def reload_config(self, ctx: commands.Context):
        try:
            self.add_commands_to_bot()
        except Exception as e:
            fail("Unable to reload the commands.", cause=e)
        else:
            await ctx.message.add_reaction("✅")


def create_play_cog(all_assets: PlayCogCommandStructure) -> commands.Cog:
    """Generate a new cog containing commands that play audio."""
    audio = AudioCreator(all_assets)

    cog_dict = {}
    for command_name, data in all_assets.items():
        max_countdown = max(data.keys())
        command = create_play_cog_command(command_name, audio, max_countdown)
        cog_dict[command_name] = command

    NewCog = type(COG_NAME, (commands.Cog,), cog_dict)
    cog = NewCog()
    return cog


def create_play_cog_command(
    command_name: str,
    audio_creator: AudioCreator,
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
            audio_creator,
            max_countdown,
        )

    return play


async def play_audio(
    ctx: commands.Context,
    seconds: int,
    command_name: str,
    audio_creator: AudioCreator,
    max_countdown: int,
) -> None:
    """Play audio in the message author's voice channel."""
    if seconds > max_countdown:
        logger.error(f"Number to count from was greater than the maximum allowed.")
        fail(f"Too long, use a number under {max_countdown}.")

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
        audio_bytes = audio_creator.new(seconds, command_name)
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
