[Deutsch](README.md) | [English](README.en.md) | [Changelog](CHANGELOG.md) | [TODO](TODO.en.md)

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

## Status

Early. What already works:

```
spielraum umgebung      # what does SPIELRaum find on this machine?
spielraum profile       # which game profiles are set up?
spielraum pruefen FILE  # check a profile file for errors
spielraum aufraeumen    # look for journals left behind
```

`spielraum starten` — the command this is all actually about — is not there
yet. It is deliberately not offered as a placeholder: a command that looks
like it sets the machine up but does not is worse than no command at all.
See [TODO.en.md](TODO.en.md).

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

## Licence

[MIT](LICENSE)
