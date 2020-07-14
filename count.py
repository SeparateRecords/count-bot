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

assets = Path(__file__).parent / "assets"


def prefix(bot: commands.Bot, msg: discord.Message) -> List[str]:
    """Invoke with `count::`, a mention, or no prefix in `#bot` or `#count-bot`."""
    prefixes = commands.when_mentioned(bot, msg)
    prefixes.append("count::")

    # DMChannel has no `name` property.
    mention = bot.user.mention
    topic = getattr(msg.channel, "topic", mention)

    if mention in topic:
        prefixes.append("")

    return prefixes


client = commands.Bot(command_prefix=prefix)


@client.event
async def on_ready():
    logging.info(f"Bot is ready: {client.user}")
    logging.info(f"Bot ID: {client.user.id}")
    logging.info(f"Owner ID: {client.owner_id}")


@client.before_invoke
async def log_command_usage(ctx: commands.Context):
    """Log each command used, along with the author and timestamp."""
    msg = f"{ctx.author} used '{ctx.prefix}{ctx.command}' at {ctx.message.created_at}"

    if ctx.guild:
        guild = ctx.guild
        channel = ctx.channel
        msg += f" in #{channel} ({channel.id}) of '{guild}' ({guild.id})"
    else:
        msg += f" in a DM"

    logging.info(msg)


@client.command()
@commands.guild_only()
async def start(ctx: commands.Context):
    """Start counting down from 3 in your voice channel (alias for 'from 3')."""
    if not ctx.invoked_subcommand:
        await start_from(ctx, 3)


@client.command(name="from")
@commands.guild_only()
async def start_from(ctx: commands.Context, begin: int):
    """Start counting down from a given number in your voice channel (max = 5, min = 0)"""
    if ctx.voice_client is not None:
        return await ctx.send("I'm already counting, please wait until I'm done!")

    if begin not in range(6):
        return await ctx.send("I can only count down using numbers between 0 and 5 :(")

    try:
        vc: discord.VoiceClient = await ctx.author.voice.channel.connect()
    except AttributeError:
        return await ctx.send("You must be in a voice channel.")
    except discord.ClientException:
        return await ctx.send("Unable to join your voice channel.")
    except discord.opus.OpusNotLoaded:
        return await ctx.send("Opus isn't loaded.")
    except asyncio.TimeoutError:
        return await ctx.send("Timed out while connecting.")

    await asyncio.sleep(0.5)

    # The stop param is non-inclusive, offset by 1.
    for i in reversed(range(begin + 1)):
        path = assets / f"{i}.wav"
        audio = discord.FFmpegPCMAudio(str(path))

        # If it's still playing, stop it and log a warning.
        if vc.is_playing():
            vc.stop()
            logging.warning(f"{i+1}.wav is over 1 second, playback stopped.")

        # Audio plays in a separate thread, don't await it.
        vc.play(audio)
        await asyncio.sleep(1)

    # If the last file is over 1 second, sleep until it ends.
    while vc.is_playing():
        await asyncio.sleep(0.5)

    await vc.disconnect()


@client.command(aliases=["die"])
@commands.is_owner()
async def kill(ctx: commands.Context):
    await ctx.send("Closing down.")
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
