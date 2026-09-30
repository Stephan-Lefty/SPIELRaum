[Deutsch](TODO.md) | [English](TODO.en.md) | [Overview](README.en.md) | [Changelog](CHANGELOG.md)

# TODO

Running list of open points. Open items at the top. Finished ones are not
deleted but moved down, with the date they were completed.

## Open

- [ ] **Look up the environment variable for the vkd3d-proton cache.** It
  could not be found in the Proton build on this machine on 2026-09-30
  (neither under `/usr/lib` nor in `compatibilitytools.d`). The cache
  currently sits as `vkd3d-proton.cache` in the game directory, and for Road
  to Vostok that directory is on a spinning disk. Redirecting it to the SSD
  would be the second lever against that bottleneck. Source: the vkd3d-proton
  documentation, not memory.

- [ ] **Measure D3D12 against Vulkan (Road to Vostok).** The game log reports
  `Driver Detected: d3d12`; Godot 4.6.2 has Vulkan compiled in. The detour
  through vkd3d-proton might be avoidable. Whether that survives sixteen mods
  is unknown. The line sits commented out in the profile.

- [ ] **Build a .deb for Debian 13.** Explicitly requested. The package must
  not later pull PySide6 from PyPI but take the distribution's build. Note,
  lesson from MailBurg on 2026-09-14: Ubuntu, Mint, Pop!_OS and Zorin do not
  carry PySide6 in their repositories — those need a route other than the .deb.

- [ ] **Actually try it on Debian 13.** So far SPIELRaum has only run on
  Manjaro. The system detection is built for both families, but built and
  proven are two different things. This is waiting on a machine to test on.

- [ ] **A guided flow instead of separate commands.** Requested on
  2026-09-30: start the program, it finds the installed games, you click one
  and are walked through step by step — current state, proposal, test run
  with measurement, keep or discard. At the end the game launches from
  within, and afterwards the machine is as it was.

- [ ] **PySide6 interface.** Only once the command line carries its weight.
  Colours from [`assets/farben.md`](assets/farben.md), as in the other
  programs.

- [ ] **Draw an `icon.svg`.** Every version in `assets/` comes from a
  bitmap. For an interface that scales freely, a drawn shape would be better.

- [ ] **Check whether KDE on Wayland has anything to switch off at all.**
  Under X11, "disable compositing" was a real lever. Under Wayland it no
  longer exists in that form. What there is instead — allow tearing, VRR —
  has not been looked up, only assumed.

## Done

- [x] **Measuring built** (2026-09-30). `spielraum messungen` evaluates the
  MangoHud logs and compares the last two runs. The first ten seconds are
  discarded — in testing they halved the mean, because that is where shaders
  get compiled.

- [x] **`spielraum starten` built** (2026-09-30). Find the profile by Steam
  app id, create the journal, apply file changes with a backup, launch the
  game through `systemd-inhibit` and `gamemoderun`, wait, restore. Signals
  are passed on to the game so that logging out does not clean up too early.

- [x] **Restore from orphaned journals** (2026-09-30). `spielraum aufraeumen`
  now actually restores instead of only listing; `--zeigen` keeps the old
  behaviour.

- [x] **`install.sh`** (2026-09-30). Needed because the Steam launch options
  require a command Steam can find. The launcher goes to `~/.local/bin` — a
  direct link into the repository would break on paths containing spaces.

- [x] **Repository created, core verified** (2026-09-30). System detection,
  profile format, state journal and the merging of `override.cfg` are in
  place and tested. The merge was additionally verified against the real file
  on disk: the mod loader entry survives.

- [x] **MangoHud and GameMode installed** (2026-09-30). Including the 32-bit
  builds — without them MangoHud does not reach through the Steam overlay.
