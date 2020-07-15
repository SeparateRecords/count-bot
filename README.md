# Voice Count (Discord bot)

Jump to: **[Usage]**, **[Setup]**, **[License]**

[Usage]: #usage
[Setup]: #setup
[License]: #license

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
count::go
```

If you want to count from a number that _isn't_ 3, use the `go from` command.
You can only use numbers between 0 and 5 (inclusive).

```
count::go from 5
```

If you need to stop the bot, run this command (owner only).

```
count::kill
```

<img width="450px" align="right" alt="Watch & discuss movies. Use &lt;@593717174732980224&gt; to count down. Commands: 'help'" src="https://user-images.githubusercontent.com/52195359/87511345-7fe1ad80-c6b8-11ea-87ba-1a5aac608f19.png">

### Advanced

If `count::` is too cumbersome, you can mention the bot instead. Alternatively,
you can omit the prefix entirely if the channel topic mentions the bot.

See an example channel topic on the right.

<sup>[Read more on mention formatting][format].</sup>

[format]: https://discord.com/developers/docs/reference#message-formatting-formats

## Setup

You'll need Git, Python (minimum is 3.6), and **[Poetry]** to run this bot.
Some level of technical knowledge is expected. If you care enough to write a
better tutorial, send a PR!

[Poetry]: https://python-poetry.org/docs/#installation

```
git clone https://github.com/SeparateRecords/count-bot
cd count-bot
poetry install
poetry run bot --token "<YOUR_BOT_TOKEN>" --owner "<YOUR_DISCORD_ID>"
```

Instead of the CLI, you can use environment variables to store your bot's
credentials. Set the token with `COUNT_BOT_TOKEN` and the owner ID with
`COUNT_BOT_OWNER`. These can be put in a `.env` file - copy `.example.env` to
`.env` to get started.

```
cp .example.env .env
```

## License

Any other long-distance couples with at least one nerd dedicated enough to run
this are absolutely welcome to do so. Contributions are welcome, too!

This code is provided under the ISC license (as are most of my projects). It's
a simplified version of the MIT license.
