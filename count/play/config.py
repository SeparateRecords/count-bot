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

from loguru import logger
from pydub import AudioSegment


class CommandAssetsMetadata(TypedDict):
    prompt: Optional[AudioSegment]
    aliases: List[str]


CommandAssetsAudio = Dict[int, AudioSegment]


class CommandAssets(TypedDict):
    audio: CommandAssetsAudio
    metadata: CommandAssetsMetadata


CommandName = str
CommandConfigData = Dict[CommandName, CommandAssets]


def create_assets(
    config_path: Path,
    reserved_names: Collection[str],
) -> CommandConfigData:
    """Create an assets dictionary from an INI file at the given path."""

    config_path = config_path.expanduser().resolve()

    if err := file_exists(config_path):
        raise err

    ini = ConfigParser()
    ini.read(config_path)

    if err := verify_default_section(ini["DEFAULT"]):
        raise err

    commands: CommandConfigData = {}

    for name, data in ini.items():

        if name == "DEFAULT":
            continue

        name = sanitized_name(name, reserved_names, whitespace)
        commands[name] = create_command_assets(
            data=data,
            reserved_names=reserved_names,
            relative_path_root=config_path.parent,
        )

    return commands


def create_command_assets(
    data: Mapping[str, str],
    reserved_names: Collection[str],
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
        "metadata": create_metadata(metadata, reserved_names, relative_path_root),
    }

    return assets


def create_audio(
    data: Mapping[int, str], relative_path_root: Path
) -> CommandAssetsAudio:
    """Transform a dictionary of int->str to a mapping of int->AudioSegment."""

    audio: CommandAssetsAudio = {}

    if min(data.keys()) < 0:
        raise ValueError(f"numeric keys must be positive")

    for number, audio_path in data.items():

        # allows you to override DEFAULT by leaving a key blank
        if not audio_path:
            continue

        audio_segment = path_to_audio(audio_path, os.environ, relative_path_root)
        audio[number] = audio_segment

    return audio


def create_metadata(
    data: Mapping[str, str], reserved_names: Collection[str], relative_path_root: Path
) -> CommandAssetsMetadata:
    """Create a dictionary of metadata for a specific command."""

    # shallow-copy so this can be mutated safely.
    mut_data = {k: v for k, v in data.items()}

    prompt_val = mut_data.pop("prompt", None)
    aliases_val = mut_data.pop("aliases", None)

    metadata: CommandAssetsMetadata = {
        "prompt": get_prompt(prompt_val, relative_path_root),
        "aliases": get_aliases(aliases_val, reserved_names),
    }

    # any left-over keys will be ignored, possibly a typo
    if mut_data.keys() - metadata.keys():
        logger.warning(f"Unknown key(s): {mut_data.keys()}")

    return metadata


def get_prompt(
    value: Optional[str], relative_path_root: Path
) -> Optional[AudioSegment]:
    """Transform the prompt to an audio file."""

    if not value:
        return None

    return path_to_audio(value, os.environ, relative_path_root)


def get_aliases(value: Optional[str], reserved_names: Collection[str]) -> List[str]:
    """Create a list of aliases from a string."""
    if not value:
        return []

    names = (name.strip() for name in value.split())
    return [sanitized_name(name, reserved_names, whitespace) for name in names]


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


def sanitized_name(
    name: str,
    reserved_names: Collection[str],
    remove_chars: Iterable[str],
) -> str:
    """Raise an error if the name is reserved, otherwise remove some chars."""

    if name in reserved_names:
        raise ValueError(f"name may not be any of the following: {reserved_names!r}")

    for char in remove_chars:
        name = name.replace(char, "")

    return name


def verify_default_section(data: Mapping[str, str]) -> Optional[KeyError]:
    """Check if the default section is good. Returns an exception if not."""

    disallowed_keys = {"aliases"}

    if disallowed_keys & data.keys():
        return KeyError(f"[DEFAULT] contained disallowed keys")

    return None


def file_exists(path: Path) -> Optional[FileNotFoundError]:
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"config file not found: {path}")
