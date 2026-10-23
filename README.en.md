[Deutsch](README.md) | [English](README.en.md) | [Changelog](CHANGELOG.md) | [TODO](TODO.en.md)

<img src="assets/icon-128.png" alt="SPIELRaum" width="128" align="right">

# SPIELRaum

Start a game, set the machine up for it, clean up afterwards.

SPIELRaum remembers, for each game, how the machine should be configured —
CPU governor, environment variables, launch arguments, and where needed a
settings file belonging to the game itself. It applies that on launch and
takes it back when the game exits. Whatever was there before is there again
afterwards.

**For Arch/Manjaro and Debian 13.** Both are intended from the outset, not as
an afterthought. No path and no tool is hard-wired; SPIELRaum looks around on
startup and tells you what is missing and how to get it.

## What it does *not* reinvent

For the part that needs system privileges — raising the CPU governor, putting
the GPU into performance mode, process priority — there is
[GameMode](https://github.com/FeralInteractive/gamemode) by Feral Interactive.
That is proven code with an audited daemon behind it, and it ships in both the
Arch and the Debian repositories. Reimplementing it would mean writing a worse
version of the same program.

SPIELRaum builds on top and does what GameMode does not:

| GameMode | SPIELRaum |
|---|---|
| one profile for everything | one profile **per game** |
| system knobs | plus environment, launch arguments, game files |
| restores on exit | restores on exit, **and after a crash** |
| — | measures whether it actually helped |

## Setting it up

```
./install.sh
```

The script first checks what is missing on this machine and offers to install it, using your distribution's package manager. Pass `--ja` to skip the prompt.

**In detail:** [docs/installation.en.md](docs/installation.en.md) for Arch/Manjaro, Debian 13 and Ubuntu.

Creates a Python environment inside the repository, installs SPIELRaum into
it and places a launcher in `~/.local/bin`. None of this needs system
privileges and nothing lands outside `$HOME`. Bundled profiles are copied to
`~/.config/spielraum/spiele`; existing ones are left alone.

## Using it

In the game's Steam launch options:

```
spielraum starten %command%
```

That is all. SPIELRaum recognises the game by `SteamAppId`, applies its
profile, launches, waits and cleans up afterwards. With no profile the game
starts unchanged — whoever adds SPIELRaum and later deletes the profile
should not end up facing a game that no longer launches.

To see what would happen first:

```
spielraum starten --profil road-to-vostok.toml --trocken -- /path/to/game
```

The remaining commands are for looking around:

```
spielraum spiele        # what is installed, and is it on an SSD?
spielraum messungen     # what has been measured, and what did it gain?
spielraum umgebung      # what does SPIELRaum find on this machine?
spielraum profile       # which game profiles are set up?
spielraum pruefen FILE  # check a profile file for errors
spielraum aufraeumen    # restore what a crash left behind
```

The commands are German, as is the rest of the program. Translating them
would mean two sets of names for the same thing, and the mistake would
surface at the worst moment — in a launch option that someone typed months
ago and no longer remembers.

## A profile

A profile is one TOML file per game. It states *what* should be the case,
drawn from a fixed list of known knobs.

```toml
[spiel]
name         = "Road to Vostok"
steam_app_id = 1963610
engine       = "godot"

[system]
gamemode      = true
nicht_stoeren = true

[umgebung]
__GL_SHADER_DISK_CACHE_SIZE = "4294967296"

[start]
argumente = ["--rendering-driver", "vulkan"]
```

**Profiles contain no commands.** A field you could write a command line into
would be a way in: whoever may write the file would then be running code with
elevated privileges. The *how* lives in the program, not in the configuration.

## Measuring instead of believing

Without measurements, every optimisation is a guess. SPIELRaum therefore has
MangoHud write a log per run and derives the mean and the 1% lows from it —
those are what you feel as stutter, and they are why a good average can still
feel rough.

This will not make it a self-tuner. That would need a reproducible scene,
which few games offer. What it does give you is a logbook across ordinary play
sessions — and with it a real before-and-after instead of "feels better".

**The first ten seconds do not count.** Measured on a twenty-second run: the
mean is 102.3 frames per second once the warm-up is excluded, and 50.8 across
the whole run. That is where the game compiles shaders and loads — measure it
and you are measuring the loading time. See [docs/messen.md](docs/messen.md)
(German).

## What it restores afterwards

The hard part is not the tuning but the promise that afterwards things are as
they were. Even if the game crashes. Even if the machine loses power. Four
nets for that:

1. Before any change the old value is read and written to the journal — only
   then is anything changed.
2. The journal lives on disk, not in memory.
3. It is written atomically. A half-written journal is worse than none: it
   looks valid.
4. On the next start, orphaned journals are picked up.

## Licence

[MIT](LICENSE)
