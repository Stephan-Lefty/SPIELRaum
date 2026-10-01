[Deutsch](TODO.md) | [English](TODO.en.md) | [Overview](README.en.md) | [Changelog](CHANGELOG.md)

# TODO

Running list of open points. Open items at the top. Finished ones are not
deleted but moved down, with the date they were completed.

## Open

- [ ] **Build the measurement run.** Drafted 2026-10-01, see
  [docs/messfahrt.md](docs/messfahrt.md) (German). One button, three runs of
  ten minutes each, with SPIELRaum switching settings in between. The hard
  part is not the measuring but that SPIELRaum does not run between two
  sessions — it needs a run record on disk that outlives several game
  starts, including the original state for aborting.

  Prerequisites: variants in the profile format, wiring up
  `art = "godot-tres"` (the reader landed today), buttons in the interface.

- [ ] **Make frame rates comparable in a meaningful way.** Measured on
  2026-10-01: within a *single* run the frame rate swung from 30.9 to 53.8 –
  74 %, purely from where the player stood. The difference between hard disk
  and SSD was 16 %, between D3D12 and Vulkan 0.6 %. The noise is larger than
  anything we set out to measure.

  SPIELRaum measures load times reliably and frame rates only roughly. See
  [docs/messen.md](docs/messen.md) (German). Possible routes: show the
  distribution across many runs instead of single means; compare sections of
  equal GPU load; treat games with a built-in benchmark separately.

- [ ] **Look up the environment variable for the vkd3d-proton cache.** It
  could not be found in the Proton build on this machine on 2026-09-30.
  Less urgent since the game moved to the SSD, and moot for Road to Vostok
  specifically — that one now runs on Vulkan directly, so vkd3d-proton is
  out of the picture. Still relevant for other games.

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

- [ ] **Node.js 20 in the actions.** GitHub has reported since the first run
  on 2026-09-30 that `actions/checkout@v4` and `actions/setup-python@v5`
  target Node.js 20 and are being forced onto 24. Still works, will break
  eventually. Affects every repository alike — better done in one sweep.

- [ ] **Check whether KDE on Wayland has anything to switch off at all.**
  Under X11, "disable compositing" was a real lever. Under Wayland it no
  longer exists in that form. What there is instead — allow tearing, VRR —
  has not been looked up, only assumed.

## Done

- [x] **D3D12 measured against Vulkan** (2026-09-30). Result: **no
  difference** — 49.0 against 49.3 frames per second is noise. The
  assumption that the detour through vkd3d-proton costs performance is
  refuted for this game on this card. Vulkan stays on anyway; it costs
  nothing either.

- [x] **Road to Vostok moved to the SSD** (2026-09-30). What held across both
  runs: 24 to 25 seconds of loading and stutters while streaming. Measuring
  the disk itself gave 112 MB/s and 7.76 ms per seek against 509 MB/s and
  0.13 ms on the SSD. **Confirmed on 2026-10-01: load time down from 23.8 to
  6.6 seconds**, against a prediction of 6 to 9. Frame rate and stutters, by
  contrast, did not change – counter to the prediction, see the point on
  measurability above.

- [x] **Published to GitHub** (2026-09-30), private for now. Alpha, proven on
  exactly one machine, never run on Debian — going public is a one-click
  step later, going back is not.

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
