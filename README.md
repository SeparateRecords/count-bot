# Voice Count (Discord bot)

Jump to: **[Usage]**, **[Setup]**, **[Audio]**, **[Contributions & Licence]**

[Usage]: #usage
[Setup]: #setup
[Audio]: #audio
[Contributions & Licence]: #contributions--license

I watch a lot of movies with my girlfriend, using Discord for voice chat. We
count down from 3 to start watching at the same time, but because of the delay
between speaking, sending the data to Discord's servers, receiving it, and
clicking play, we can end up out of sync by up to a second - this means one of
us can be laughing at a joke the other hasn't heard yet.

We needed *something* else to keep both of us in sync - using a Discord bot,
we should receive the packets at roughly the same time... theoretically.

Music bots exist, and yeah, using one is totally an option! To me, it just
feels like a hack to upload audio to YouTube and play it with a bot that wasn't
designed for this purpose. You don't get as much control over the counting,
and the chat logs are messy. If you don't care, go for it!

## Usage

You must be in a voice channel the bot can join.

To count down from 3, run this command.

```
.go
```

If you want to count from a number that _isn't_ 3, use the `go in` command.
You can only use numbers between 0 and 5 (inclusive).

```
.go in 5
```

To say "Pause" instead of "Go", use `pause` instead of `go`.

```
.pause in 2
```

If you need to stop the bot, run this command (owner only).

```
.kys
```

## Setup

You'll need FFmpeg, Git, Python (minimum is 3.6), and **[Poetry]** to run this
bot. Some level of technical knowledge is expected. If you care enough to write
a better tutorial, send a PR!

[Poetry]: https://python-poetry.org/docs/#installation

```
git clone https://github.com/SeparateRecords/count-bot
cd count-bot
poetry install
poetry run bot --token "YOUR_BOT_TOKEN" --owner "YOUR_DISCORD_ID"
```

Instead of the CLI, you can use environment variables to store your bot's
credentials. Set the token with `COUNT_BOT_TOKEN` and the owner ID with
`COUNT_BOT_OWNER`. These can be put in a `.env` file - copy `.example.env` to
`.env` to get started.

```
cp .example.env .env
```

## Audio

You can use the `custom_audio/` directory to override the sound files in
`default_audio/` without replacing or changing them. Here are the file names
you can override:

* `5.wav`
* `4.wav`
* `3.wav`
* `2.wav`
* `1.wav`
* `0.wav`

All the audio files must be under 1 second in length. After 1 second, playback
will be cut off and a warning will be logged, although it will continue
counting fine. The only exception to this is `0.wav` - it can be over 1 second.

## Contributions & License

Any other long-distance couples with at least one nerd dedicated enough to run
this are absolutely welcome to do so. Contributions are welcome!

This code is provided under the ISC license (as are most of my projects). It's
a simplified version of the MIT license.
