# Voice Count: Assets

The following audio files must be present in `default/`.

- `5.wav`
- `4.wav`
- `3.wav`
- `2.wav`
- `1.wav`
- `0.wav`

These can be overridden without modifying the originals by putting an
identically named file in `custom/`. For example, `custom/0.wav` will play when
`default/0.wav` would normally play.

The final audio file, `0.wav`, can be over 1 second. Any other audio files over
1 second will be stopped before the next file plays, with a warning logged.

Feel free to replace these files with your own! My microphone is old and
crappy, and my room is like a cave.
