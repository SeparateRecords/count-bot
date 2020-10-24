# Audio configuration

## Documentation

The numbers correspond to the audio file that will be played on that second
during the countdown. The file paths may be absolute or relative, and include
environment variables (`$var`/`${var}`).

The title of each section (excluding `DEFAULT`) is a command that will be
generated when the config is loaded.

### Overriding values

To override a default value, leave it blank.

```ini
[kart]
5 =
4 =
3 = beep-short.wav
2 = beep-short.wav
1 = beep-short.wav
0 = beep-long.wav
```

### Default starting number

The default start is the greatest number specified, clamped at 3. In
this example, running 'race' without arguments will play 2, 1, 0.

```ini
[race]
5 =
4 =
3 =
2 = ready.wav
1 = set.wav
0 = gooooo.wav
```

### Omitting numbers

Blank numbers less than the greatest number specified will be left silent.

```ini
[monkey-ball]
5 =
4 =
3 =
2 = monkeyball-ready.mp3
1 =
0 = monkeyball-go.wav
```
