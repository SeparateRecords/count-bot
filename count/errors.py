from __future__ import annotations

from typing import NoReturn, Optional, Type

import discord
import discord.ext.commands as commands


class ShowFailureInChat(commands.CommandError):
    """Escape a function early and leave a message for the user.

    If __cause__ is set, `on_command_error` will raise it.
    """

    def __init__(self, message: object):
        super().__init__(str(message))

    def embed(self):
        return discord.Embed(description=f"**Error:** {self}", color=0xE94545)


def fail(
    message: str,
    *,
    err: Type[commands.CommandError] = ShowFailureInChat,
    cause: Optional[BaseException] = None,
) -> NoReturn:
    raise err(message) from cause
