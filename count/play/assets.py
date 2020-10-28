from __future__ import annotations

import os
from configparser import ConfigParser
from pathlib import Path
from string import Template, whitespace
from typing import Dict, Mapping

from pydub import AudioSegment

CommandAssets = Dict[int, AudioSegment]
PlayCogCommandStructure = Dict[str, CommandAssets]


def config_to_assets(config_path: Path) -> PlayCogCommandStructure:
    """Create an assets dictionary from an INI file at the given path."""
    config_path = config_path.expanduser().resolve()

    if not config_path.exists():
        raise FileNotFoundError(config_path)

    if not config_path.is_file():
        raise IsADirectoryError(config_path)

    # Required because paths in config files are relative to the config
    # file's directory, not the current working directory.
    relative_path_root = config_path.parent

    c = ConfigParser()
    c.read(config_path)

    commands: PlayCogCommandStructure = {}

    for section_name, section_data in c.items():
        if section_name == "DEFAULT":
            continue

        if any(char in whitespace for char in section_name):
            raise KeyError(f"Command names may not contain whitespace.")

        assets = create_command_assets(section_data, relative_path_root)
        commands[section_name] = assets

    return commands


def create_command_assets(
    command_data: Mapping[str, str],
    relative_path_root: Path,
) -> CommandAssets:
    """Get assets of a specific command."""

    command_assets = {}

    for key, value in command_data.items():
        if not value:
            continue

        number = key_to_number(key)
        audio = path_to_audio(value, relative_path_root)
        command_assets[number] = audio

    return command_assets


def key_to_number(key: str) -> int:
    """Transform a key to a number and validate it."""
    number = int(key)
    if number < 0:
        raise ValueError(f"key {key} is negative")
    return number


def path_to_audio(path: str, relative_path_root: Path) -> AudioSegment:
    """Perform transformations on the path to create an AudioSegment."""

    try:
        substituted = Template(path).substitute(os.environ)
    except KeyError as cause:
        raise KeyError(f"Failed to substitute a variable: {cause}") from cause

    asset_path = Path(substituted).expanduser()

    if asset_path.is_absolute():
        audio_file = asset_path
    else:
        audio_file = relative_path_root / asset_path

    if not audio_file.exists():
        raise FileNotFoundError(audio_file)

    if not audio_file.is_file():
        raise IsADirectoryError(audio_file)

    segment = AudioSegment.from_file(audio_file)
    return segment
