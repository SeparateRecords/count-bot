from __future__ import annotations

import os
from configparser import ConfigParser
from pathlib import Path
from string import Template, whitespace
from typing import (
    Collection,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    TypedDict,
)

from pydub import AudioSegment


CommandAssetsAudio = Dict[int, AudioSegment]


class CommandAssetsMetadata(TypedDict):
    prompt: Optional[AudioSegment]
    aliases: List[str]


class CommandAssets(TypedDict):
    audio: CommandAssetsAudio
    metadata: CommandAssetsMetadata


CommandName = str
PlayCogCommandStructure = Dict[CommandName, CommandAssets]


def sanitize_section_name(
    name: str,
    reserved_names: Collection[str] = (),
    remove_chars: Iterable[str] = (),
) -> str:
    """Raise an error if the name is reserved, otherwise remove some chars."""

    if name in reserved_names:
        raise ValueError(f"name may not be any of the following: {reserved_names!r}")

    for char in remove_chars:
        name = name.replace(char, "")

    return name


def create_assets(
    config_path: Path,
    reserved_names: Collection[str],
) -> PlayCogCommandStructure:
    """Create an assets dictionary from an INI file at the given path."""
    config_path = config_path.expanduser().resolve()

    if not config_path.exists() or not config_path.is_file():
        raise FileNotFoundError(f"config file not found: {config_path}")

    # Required because paths in config files are relative to the config
    # file's directory, not the current working directory.
    relative_path_root = config_path.parent

    c = ConfigParser()
    c.read(config_path)

    commands: PlayCogCommandStructure = {}

    for section_name, section_mapping in c.items():
        if section_name == "DEFAULT":
            continue

        assets = create_command_assets(section_mapping, relative_path_root)
        sanitized_name = sanitize_section_name(section_name, reserved_names, whitespace)
        commands[sanitized_name] = assets

    return commands


def create_command_assets(
    data: Mapping[str, str],
    relative_path_root: Path,
) -> CommandAssets:
    """Get assets of a specific command."""
    numeric: Dict[int, str] = {}
    metadata: Dict[str, str] = {}

    for k, v in data.items():
        if k.isnumeric():
            numeric[int(k)] = v
        else:
            metadata[k] = v

    assets: CommandAssets = {
        "audio": create_audio(numeric, relative_path_root),
        "metadata": create_metadata(metadata, relative_path_root),
    }

    return assets


def create_audio(
    data: Mapping[int, str], relative_path_root: Path
) -> CommandAssetsAudio:
    """Transform a dictionary of int->str to a mapping of int->AudioSegment."""
    d: CommandAssetsAudio = {}

    if min(data.keys()) < 0:
        raise ValueError(f"numeric keys must be positive")

    for number, audio_path in data.items():

        # allows you to override DEFAULT by leaving a key blank
        if not audio_path:
            continue

        audio = path_to_audio(audio_path, os.environ, relative_path_root)
        d[number] = audio

    return d


def create_metadata(
    data: Mapping[str, str], relative_path_root: Path
) -> CommandAssetsMetadata:
    """Create a dictionary of metadata for a specific command."""
    metadata: CommandAssetsMetadata = {
        "prompt": process_prompt_key(data.get("prompt"), relative_path_root),
        "aliases": process_aliases_key(data.get("aliases")),
    }

    all_keys = set(data.keys())
    if all_keys.difference(metadata.keys()):
        raise KeyError(f"Unknown key(s): {all_keys}")

    return metadata


def process_prompt_key(
    value: Optional[str], relative_path_root: Path
) -> Optional[AudioSegment]:
    """Transform the prompt to an audio file."""
    if not value:
        return None
    return path_to_audio(value, os.environ, relative_path_root)


def process_aliases_key(value: Optional[str]) -> List[str]:
    """Create a list of aliases from a string."""
    if not value:
        return []

    names = (name.strip() for name in value.split())
    return [sanitize_section_name(name) for name in names]


def path_to_audio(
    path: str, vars: Mapping[str, str], relative_path_root: Path
) -> AudioSegment:
    """Try to convert a path into an AudioSegment."""
    try:
        substituted = Template(path).substitute(vars)
    except KeyError as cause:
        raise KeyError(f"Failed to substitute a variable: {cause}") from cause

    asset_path = Path(substituted).expanduser()

    if asset_path.is_absolute():
        audio_file = asset_path
    else:
        audio_file = relative_path_root / asset_path

    if not audio_file.exists() or not audio_file.is_file():
        raise FileNotFoundError(f"{audio_file} is not a file, can't convert to audio")

    return AudioSegment.from_file(audio_file)
