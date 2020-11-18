from __future__ import annotations

from copy import deepcopy
from typing import Dict, Tuple

from pydub import AudioSegment

from .config import CommandConfigData


def safe_for_discord(audio: AudioSegment) -> AudioSegment:
    """
    `VoiceClient.play` expects stereo, 48kHz, 16-bit, PCM audio.
    AudioSegment data is already PCM, but the other properties must be
    normalized to avoid playback issues.
    """
    return audio.set_frame_rate(48000).set_sample_width(2).set_channels(2)


class Counter:
    """Create audio that never stutters by dynamically combining files."""

    def __init__(self, assets: CommandConfigData) -> None:
        # Using a cache to avoid the (possibly) expensive duplicate
        # work. The only way the cache can become invalid is if the dict
        # gets mutated, copy it to ensure there are no other references
        # to it.
        self._assets = deepcopy(assets)
        self._cache: Dict[Tuple[int, str], bytes] = {}

    def __call__(self, seconds: int, command: str) -> bytes:
        """Generate PCM audio bytes by combining stored audio data.

        Raises `KeyError` if `command` is not an asset.
        """
        if command not in self._assets:
            raise KeyError(f"The command ({command}) is not a stored asset.")

        cache_key = (seconds, command)
        command_assets = self._assets[command]

        if cache_key in self._cache:
            return self._cache[cache_key]

        audio = AudioSegment.silent(duration=1000 * seconds)

        # the length of the audio ends up being the length of the count,
        # plus the length of the 0-sound if it exists.
        final_sound = command_assets["audio"].get(0)
        if final_sound:
            audio += final_sound

        # this allows audio clips to be as long as necessary. anything
        # over 1 second will overlap with the following audio.
        for i in range(seconds, 0, -1):
            sound = command_assets["audio"].get(i)
            if not sound:
                continue
            position_ms = (seconds - i) * 1000
            audio = audio.overlay(sound, position=position_ms)

        pcm_bytes = safe_for_discord(audio).raw_data
        self._cache[cache_key] = pcm_bytes
        return pcm_bytes
