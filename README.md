# count-bot

Jump to: **[Usage]**, **[Setup]**, **[Audio]**, **[Contributions & Licence]**

[Usage]: #usage
[Setup]: #setup
[Audio]: #audio
[Contributions & Licence]: #contributions--license

**`count-bot`** is a powerful *(read: over-engineered)* solution to
watch-party syncing issues.

I watch a lot of movies with my girlfriend, and it's annoying having to
manually sync Netflix so we both see and react to stuff at the same
time. Music bots are an option but it feels hacky using one for this
purpose. **`count-bot`** is purpose built: it counts down. That's all.

## Usage

You must be in a voice channel the bot can join.

To count down from 3 and say "Go", run this command.

```
.go
```

If you want to count from a number that *isn't* 3, use a number after
the command. You can only use numbers between 5 and 0 (inclusive).

```
.go 5
```

To say "Pause" instead of "Go", use `.pause` instead of `.go`. Simple!

```
.pause
```

If you need to stop the bot, run this command (owner only).

```
.kys
```

## Setup

You'll need FFmpeg, Git, Python, **[Poetry]**, and some level of
technical knowledge to run this bot. If you care enough to write a
better tutorial, send a PR!

Your bot will need the "members" intent.

As of writing (2020-10-28), there are no PyNaCL wheels for Python 3.9.
You can either compile libsodium yourself, or just use Python 3.8
([see: `poetry env use <executable>`][env]).

[Poetry]: https://python-poetry.org/docs/#installation
[env]: https://python-poetry.org/docs/managing-environments/#switching-between-environments

```
git clone https://github.com/SeparateRecords/count-bot
cd count-bot
poetry env use "/path/to/your/python38"
poetry install
```

Once installed, you can use the CLI from within the directory.

```
poetry run count-bot --token "MY_BOT_TOKEN"
```

Instead of the CLI, you can use environment variables or a `.env` file
to store your bot's configuration. See the [.example.env] file for all
the allowed values.

[.example.env]: .example.env

```
cp .example.env .env
```

You'll be prompted for a token when running `count-bot` if there is no
token specified through the CLI or environment.

<details>
<summary><strong>Audio customization</strong></summary>

Create a copy of `count/assets` in the project directory.

```
count-bot> cp -r count/assets assets
```

Configure the bot to use the custom configuration file (it's included
in the directory you copied). You will need to restart the bot
completely once you've done this.

```
echo "COUNT_BOT_CUSTOM_CONFIG=assets/config.ini" >> .env
```

Now we can modify the file. This is what it looks like by default.

```ini
[DEFAULT]
5 = 5.wav
4 = 4.wav
3 = 3.wav
2 = 2.wav
1 = 1.wav

[go]
0 = go.wav

[pause]
0 = pause.wav
```

Each section header, except for `DEFAULT`, is a command. Command names
can contain any character except for whitespace. The values from
`DEFAULT` automatically populate each section unless they're explicitly
overridden.

When each number is reached in the countdown, the corresponding audio
file is played.

<details>
<summary>
Here's an an example of a pointlessly confusing command.
</summary>

```ini
[DEFAULT]
5 = 5.wav
4 = 4.wav
3 = 3.wav
2 = 2.wav
1 = 1.wav

[go]
0 = go.wav

[pause]
0 = pause.wav

# 4 won't inherit from DEFAULT because it's blank
[confuse-me]
5 = 4.wav
4 =
3 = 3.wav
2 = pause.wav
1 = 2.wav
0 = go.wav
```

</details><br><!-- END POINTLESS EXAMPLE -->

You can use any file name you like, as long as it points to a valid
audio file that ffmpeg knows how to read. The files can be relative or
absolute. File paths may start with a `~`, and can contain environment
variables using `$var` and `${var}` templates.

To reload the commands from the current config file, use this command
(owner only)

```
.ext reload play
```

</details><br><!-- END AUDIO CUSTOMISATION -->

## Contributions & License

Any other long-distance couples with at least one nerd dedicated enough
to run this are absolutely welcome to do so. Contributions are welcome!

This code is provided under the ISC license (as are most of my
projects). It's a simplified version of the MIT license.
