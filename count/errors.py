from __future__ import annotations

from typing import NoReturn, Optional, Type

import discord.ext.commands as commands


class ShowFailureInChat(commands.CommandError):
    """Escape a function early and leave a message for the user.

    If __cause__ is set, `on_command_error` will raise it.
    """

    def __init__(self, message: object):
        super().__init__(str(message))

    def __str__(self):
        return f"**Error:** {super().__str__()}"


def fail(
    message: str,
    *,
    err: Type[commands.CommandError] = ShowFailureInChat,
    cause: Optional[BaseException] = None,
) -> NoReturn:
    raise err(message) from cause
