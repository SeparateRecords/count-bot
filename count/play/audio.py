from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Tuple

from pydub import AudioSegment

if TYPE_CHECKING:
    from count.play.assets import PlayCogCommandStructure


class Countdown:
    """Create audio that never stutters by dynamically combining files."""

    def __init__(self, assets: PlayCogCommandStructure) -> None:
        # Using a cache to avoid the potentially expensive duplicate
        # work. The only way the cache can become invalid is if the
        # data source gets mutated. Deep-copying the data ensures
        # there's no references to it, so the cache is always valid.
        self._assets: PlayCogCommandStructure = {
            key: {**values} for key, values in assets.items()
        }
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

        audio = AudioSegment.silent(duration=1000 * seconds, frame_rate=48000)

        # doing this first allows longer audio to overlap with it.
        final_sound = command_assets.get(0)
        if final_sound:
            audio += final_sound

        # this method allows audio clips to be as long as necessary.
        # audio over 1 second will overlap with the following audio.
        for i in range(seconds, 0, -1):
            sound = command_assets.get(i)
            if not sound:
                continue
            position_ms = (seconds - i) * 1000
            audio = audio.overlay(sound, position=position_ms)

        # discord.py expects stereo, 48kHz, 16-bit (2 byte) audio for
        # normal playback. The audio frame rate is already set to 48kHz,
        # but pydub will increase it if there's a single segment higher.
        # <48000 plays back too fast, >48000 plays back too slow.
        normal = audio.set_frame_rate(48000).set_sample_width(2).set_channels(2)

        pcm_audio = normal.raw_data

        self._cache[cache_key] = pcm_audio  # type: ignore

        return pcm_audio  # type: ignore
