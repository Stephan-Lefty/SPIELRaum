# Installing SPIELRaum

For Arch/Manjaro, Debian 13 and Ubuntu. SPIELRaum itself needs no root
privileges — only the surrounding packages come from the package manager.

> **How well tested is this?** SPIELRaum is developed and used daily on
> Manjaro. CI additionally runs on Ubuntu. **It has never run on an actual
> Debian 13 machine** — the Debian steps below are written carefully but
> untested. If something breaks, that is a bug here, not on your end.
> Please report it.

## 1. Prerequisites

SPIELRaum itself only needs Python 3.11 or newer — that is when `tomllib`
entered the standard library. Everything else is optional: if a tool is
missing, exactly that one knob drops out, and SPIELRaum tells you which one
and how to install it.

### Arch / Manjaro

```
sudo pacman -S git python pyside6
```

For the knobs:

```
sudo pacman -S gamemode mangohud keyd
```

### Debian 13 / Ubuntu

```
sudo apt install git python3 python3-venv python3-pyside6.qtwidgets
```

For the knobs:

```
sudo apt install gamemode mangohud keyd
```

> **Check before it fails:** `keyd` is not in every release of the
> repositories. `apt-cache policy keyd` will tell you. If it is missing,
> everything else still works — only the per-game key mapping drops out.

> **About the PySide6 package name:** On Debian 13 it is called
> `python3-pyside6.qtwidgets`. If `apt` cannot find it, try
> `apt-cache search pyside6`. This is the most likely stumbling block,
> because it has never been verified on an actual Debian machine.

**Why PySide6 from the distribution and not from pip?** The distribution
package is built against the Qt that is on the machine. A pip-installed
PySide6 brings its own Qt — 150 MB that can clash with the system one.
That is why `install.sh` creates the virtual environment with
`--system-site-packages`, so the distribution package stays visible.

## 2. Install

```
git clone https://github.com/Stephan-Lefty/SPIELRaum.git
cd SPIELRaum
./install.sh
```

The script creates:

| where | what |
|---|---|
| `SPIELRaum/.venv` | a dedicated Python environment |
| `~/.local/bin/spielraum` | the command-line launcher |
| `~/.local/bin/spielraum-ui` | the GUI launcher |
| `~/.local/share/applications` | the application menu entry |
| `~/.config/spielraum/spiele` | the bundled profiles |

Existing profiles are left alone. Anyone who has tweaked one does not want
it overwritten on the next install.

If the script reports that `~/.local/bin` is not on your PATH, add this to
`~/.bashrc` or `~/.zshrc`:

```
export PATH="$HOME/.local/bin:$PATH"
```

## 3. Verify

```
spielraum umgebung
```

Shows what SPIELRaum found on this machine and what is missing — with the
install command for your distribution family next to it.

```
spielraum spiele
```

Lists installed Steam games and says which ones have a profile.

## 4. Tell Steam about it

For every game SPIELRaum should accompany, in its **launch options**:

```
spielraum starten %command%
```

Without this, Steam starts the game directly and SPIELRaum sees nothing: no
measurement, no key mapping, no restoring afterwards.

## 5. Per-game key mapping (optional)

Only needed if the profile contains a `[tasten]` section. One-time setup:

```
sudo usermod -aG keyd $USER
sudo systemctl enable --now keyd
```

Then **properly log out and back in** — not just lock the screen. Group
memberships are established at login, and every process inherits them from
there. Verify with:

```
id | grep keyd
```

If you see `946(keyd)` or any number followed by `(keyd)`, you are set.

Details in [tasten.md](tasten.md) (German).

## Troubleshooting

**`python3 -m venv` fails.** On Debian and Ubuntu, venv lives in its own
package: `sudo apt install python3-venv`.

**The GUI will not start.** Either PySide6 is missing, or it is invisible
to the virtual environment. Check:

```
.venv/bin/python3 -c "import PySide6; print(PySide6.__file__)"
```

If you get an `ImportError` although the package is installed, the
environment was created without `--system-site-packages`. Run
`./install.sh` again — it flips the switch in `.venv/pyvenv.cfg` rather
than throwing the environment away.

**`spielraum` is not found.** `~/.local/bin` is not on your PATH, see above.

**The game starts but nothing happens.** SPIELRaum found no profile.
`spielraum spiele` shows which games have one. A profile must live in
`~/.config/spielraum/spiele`, not in the repository's `profile/` folder —
that one only holds the templates.

## Uninstalling

```
rm -rf ~/.local/bin/spielraum ~/.local/bin/spielraum-ui
rm -f  ~/.local/share/applications/spielraum.desktop
rm -rf ~/.config/spielraum ~/.local/share/spielraum
```

Then delete the cloned directory. The Steam launch options have to be
removed by hand — otherwise the game will not start, because the command
is gone.
