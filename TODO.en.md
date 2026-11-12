[Deutsch](TODO.md) | [English](TODO.en.md) | [Overview](README.en.md) | [Changelog](CHANGELOG.md)

# TODO

Running list of open points. Open items at the top. Finished ones are not
deleted but moved down, with the date they were completed.

## Open

- [ ] **Why do MangoHud's keybinds not work?** Asked for on 2026-11-12:
  move the overlay while playing. MangoHud 0.8.4 has
  `toggle_hud_position` and `toggle_hud` for that, SPIELRaum sets both — in
  Road to Vostok nothing happened.

  I had reported this as done because the option is listed in
  `/usr/share/doc/mangohud/MangoHud.conf.example`. What that confirmed was
  the spelling, not that it does anything. The same half step as with
  `PROTON_USE_XALIA` on 2026-11-09.

  Ruled out:

  * **Not the spelling.** MangoHud accepts the lines without complaint,
    checked with `vkcube` and the same `MANGOHUD_CONFIG`.
  * **Not a missing input path.** `libMangoHud.so` links
    `libwayland-client.so.0` and `libxkbcommon.so.0` and loads
    `libX11.so.6` on demand; that one is present on this machine.

  Still to check, in this order:

  1. Whether the keybinds work in a **native** game. Vostok runs under
     Proton and is therefore an XWayland window; a native Wayland game would
     take the other path. That separates "MangoHud cannot" from "not under
     XWayland".
  2. Whether **keyd** gets in the way. It grabs the keyboard device and
     emits through its own; whether MangoHud sees that is untested. A run
     with the mapping withdrawn answers it.
  3. Whether **Steam** swallows F12 — that is its screenshot key. Affects
     only `toggle_hud`, not the move.
  4. Whether `PROTON_ENABLE_WAYLAND=1` helps. That changes the display path
     of the whole game and therefore belongs after the other three, not
     before.

  Until then SPIELRaum no longer promises the keybinds. They stay set,
  because they cost nothing.

  **The replacement was built on 2026-11-12:** two fields in the interface,
  bottom right next to "Anzeige:" — where the overlay sits and how much it
  shows, including "nothing". Both only take effect on the next start, but
  they solve the actual problem. What stays open is only why the keybinds do
  not work.

  Measured in passing, and it belongs here because it nearly went wrong:
  **MangoHud's `no_display` also stops the logging.** Two runs with
  `vkcube` — zero logged lines against 55 for the other two extents. Had I
  assumed that the way I assumed the keybinds, "overlay off" would have
  become a setting that silently prevents every measurement.

  **And what could be built instead:** switching the corner from the
  interface rather than editing the profile file. It only takes effect on the
  next start, but it solves the actual problem — the overlay is in the way
  and should go somewhere else.

- [ ] **Hook up a second mod loader source.** `modloader.QUELLEN` knows one
  so far, and it points at GitHub releases. The shape — read the version
  from the file, fetch the latest from a URL — should hold, but it has been
  tried on exactly one case. Only the second will show what is too rigid.

  Keep the warning in view: the Vostok loader resetting `override.cfg` on a
  version change is only harmless as long as the profile does not touch that
  file itself. The Vostok profile does not — it only touches
  `Preferences.tres`. Add an `override.cfg` knob there and we get the same
  conflict as with the keys on 2026-11-03: two programs, one file, neither
  aware of the other.

- [ ] **Record the mods alongside each measurement.** Established
  2026-11-03: measurements record the CPU governor, but not which mods ran
  at which version. For Road to Vostok that is **16 mods** reaching into
  inventory, HUD, lighting and damage calculation — the largest unrecorded
  confounder there is.

  It probably explains a contradiction in our own numbers: `optik` scored
  41.3 frames on 2026-10-01 and 48.1 on 2026-11-03. The mod set changed in
  between (ItemClarity, LM and the configuration menu are dated 10-21,
  ElegantHUD and the German translation 10-01). A comparison across that
  line does not compare two variants, it compares two different games.
  Belongs with the tolerance-band point below.

  Everything needed is local: each `.vmz` in the `mods/` folder is a ZIP
  containing a `mod.txt` with `name`, `id` and `version`. No network access.

  The mods come from <https://modworkshop.net/g/roadtovostok>; `mod.txt`
  names the id there as `[updates] modworkshop=<id>`.

  To do: record names and versions while measuring, show them in the report,
  and warn when two compared runs differ.

  **The same goes for other programs taking the GPU.** On 2026-11-04 Road to
  Vostok stalled on startup, and the cause was RustDesk — a screen captured
  and streamed on the side costs exactly the performance SPIELRaum claims to
  measure. Whether it was running during that day's measured runs can no
  longer be determined, and that is the point: a measurement where it is
  unclear what else was running is not one.

  So record what else was on the card at runtime — remote desktop, screen
  recording, a second game. The names are short, the list is available via
  `nvidia-smi` (already in the tool list), and it answers afterwards the
  question that otherwise cannot be answered at all.

  **Third case, 2026-11-12 — and this one is in none of our files.** Road to
  Vostok has always run with `--rendering-method mobile`, Godot's reduced
  renderer. The argument is in neither the Steam launch options nor the
  profile: Steam stores two launch configurations for this game, and
  `%command%` carries the arguments of whichever is chosen.

  ```
  Road to Vostok [Vulkan]          --rendering-driver vulkan
  Road to Vostok [Compatibility]   --rendering-method mobile
  ```

  Looked up in Steam's `appinfo.vdf`. It only came to light because the
  running process list happened to be in view at game start.

  Every measurement so far therefore describes the compatibility variant.
  They remain valid against each other — but they do not describe the game,
  only one of its two builds.

  **The [Vulkan] vs [Compatibility] comparison is due 2026-11-13.** For it
  to be worth anything it has to honour everything that went wrong today:

  * **Same route, same duration.** The same path both times, both laps the
    same length — otherwise it compares sessions, not renderers.
  * **Nothing running alongside.** No OBS, no remote desktop. The CPU load
    in the evaluation will show afterwards whether that held.
  * **Overlay on "only during a measurement run"**, so it measures without
    anything being in the picture.
  * **The gap has to exceed 7.6 per cent**, otherwise it is not one — see
    the point on route dependence below.

  And the result has two halves: frame rate *and* looks. A renderer that
  costs ten per cent and visibly improves the image is no loser. That is
  the user's call, not the 1 % low's.

  **To do:** record the actual command line at start. It is right there —
  SPIELRaum assembles it itself and then throws it away. That would capture
  renderer, launch arguments and Proton version in one go — more than the
  mod list and `nvidia-smi` cover together.

  **Second confirmed case, 2026-11-12 — and this time with a number.** OBS
  was recording during the measured run. It only came to light because the
  recording stopped *mid-run*; the same stretch against the 11-10 run:

  ```
  minutes  2-10, OBS running ....  39.1 against 47.2     -17.3 %
  minutes 11-12, OBS off ........  56.0 against 53.8      +4.1 %
  ```

  **17 per cent** — more than the gap between `optik` and `leistung`, and
  more than any setting in this project has ever gained.

  And the decisive part: **it is already in the measurement files.** OBS
  encoded on the CPU, so the `cpu_load` column shows it outright while GPU
  load barely moves. Means over the first twelve minutes:

  ```
  optik    11-05 .... CPU 26.1 %
  leistung 11-09 .... CPU 25.7 %
  leistung 11-10 .... CPU 28.6 %
  leistung 11-12 .... CPU 68.9 %   <- co-user, unmistakable
  ```

  In minute 11 CPU load drops from 81.8 to 38.3 per cent and the frame rate
  jumps from 48.8 to 57.7 — the moment the recording ended, as a step in
  our own data.

  **The smaller part of this was built on 2026-11-12** (0.9.0): CPU load is
  carried per run and reported, and on a comparison SPIELRaum warns when two
  runs differ by more than ten percentage points. It works **retroactively**
  on every stored run and would have thrown this one out before the
  evaluation instead of after.

  **The ten percentage points are calibrated on one game.** For Road to
  Vostok the clean runs sit within 2.9 points; for Enshrouded they span
  38.9 to 53.0 — fourteen points, with no co-user at all. So the threshold
  may be too tight for a CPU-hungry game. That is why only a *pair* gets
  compared rather than highest against lowest across many runs; otherwise
  Enshrouded would have warned on every look.

  The right answer is a spread **per game**: what varies normally for this
  game is told by its own runs. That needs several clean runs per game, and
  those exist only where measuring already happened. Until then the number
  stays a rough figure, and it is labelled as one in the code.

  What stays open is the name listing via `nvidia-smi`. `cpu_load` says
  *that* it was someone — the question deciding between a measurement and
  none. It does not say who. And a co-user that only loads the GPU and not
  the CPU goes unnoticed entirely; OBS was caught because it encoded on the
  processor.

  SPIELRaum may also **report** that mods are outdated — in the report pane,
  *before* the game starts. The comparison is cheap: 14 of the 16 mods name
  their id, and `api.modworkshop.net/mods/versions` takes up to 100 at once.
  Two conditions: a profile switch, **off** by default, because SPIELRaum
  touches the network nowhere else — and the query must never hold up the
  game start. With no network it says "not checked" and starts as always.

  **Not** to do: downloading and swapping. The game's own mod loader
  (`modloader.gd` 3.2.1) already does that — an "Updates" tab, a "Check for
  Updates" button, downloads via `api.modworkshop.net`, plus a self-check.
  And it is the part where things break: it renames the file when swapping
  (`_derive_updated_filename` reads the HTTP headers for that), honours load
  order via `priority`, and discards its hook cache when a version changes.
  Rebuilding that means risking sixteen mods to save one button press. Same
  case as GameMode, see CLAUDE.md.

  So: SPIELRaum says it, the mod loader does it.

  Two mods are beyond its reach because they carry no `[updates]` section:
  *El-Prime Armor Durability* and *MedicalDurability*. Those stay manual
  whatever gets built.

- [ ] **Two runs only become comparable once the same route was walked.**
  Equal measurement length is the minimum condition for that, not the
  solution. All that gets checked today is the ten-minute minimum.

  **Corrected twice on 2026-11-12 — and that is the actual lesson here.**
  From 11-10 this spot claimed duration alone costs 6 per cent (52.5 fps
  over 12.6 minutes against 49.4 over 96). Then it claimed the opposite,
  on the strength of a third run. But that third run had OBS recording
  alongside and is worthless as a measurement. Both versions were written
  too fast.

  All that holds up is this: within a run, the number does not drop with
  length. The same runs truncated to their own opening stretch, the one
  with a co-user left out:

  ```
  Run                  full    cut to 36 min    cut to 12 min
  optik    11-05       44.5         44.1             43.1
  leistung 11-09       52.5         52.5             52.1
  leistung 11-10       49.4         48.1             48.4
  ```

  What stays open is where the gap between 11-09 and 11-10 comes from. Cut
  to the same twelve minutes, 52.1 against 48.4 remains — 7.6 per cent. The
  gap was there from the start and is therefore not a matter of duration.
  Two sessions, two routes, one explanation: that was the flaw in the first
  version.

  So there are two things to do. The easy one: enforce equal duration, or
  truncate to the common opening stretch — `messen.auswerten` can already
  do it, only the call is missing. The hard one: a comparison that accounts
  for the route, say a fixed circuit or sections of equal GPU load pitted
  against each other. Until then 7.6 per cent is the figure below which no
  difference is a difference — which puts a number on the tolerance-band
  point below.

  And as a note to self: both wrong versions came out of **one**
  measurement with a plausible explanation next to it. That exact thing had
  already gone wrong three times in the preceding two weeks. An explanation
  that fits only one measurement is not one — and neither is a correction
  built on an unvetted measurement.

- [ ] **The measurement run needs a tolerance band.** `fahrt.beste()` simply
  takes the highest 1 % low and declares a winner, even when the gap is
  noise. On 2026-11-03 `optik` (26.54) and `leistung` (26.31) were 0.9 %
  apart — `optik` was recommended, although `leistung` delivered 12 % more
  frames at the same smoothness, measured over a 56 % longer run (longer
  runs score lower). By the project's own standard that is not a decision,
  it is noise with a decimal place.

  What is needed is a threshold below which SPIELRaum says "no difference"
  and then falls back to the mean — or gives no recommendation at all and
  just shows the numbers. The threshold has to be derived from the
  measurements, not guessed.

  Related: `ausgangszustand` in the run record was `null` on 2026-11-03,
  even though `--abbrechen` is supposed to restore that original state.

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

- [x] **The mod loader state is in the interface** (2026-11-04). The report
  shows the installed version, an amber box when something is staged, and a
  button that installs it after a confirmation. Reading is local only via
  `stand_lokal()`; a test pins down that the report never touches the
  network — a query while drawing would freeze the window.

  One assumption from this TODO corrected along the way: "the button must do
  nothing while the game is running — the file is in use then" is not true
  on Linux. Writing is atomic — write beside, then rename — so the running
  game keeps the handle it opened. It is not dangerous, merely ineffective
  until the next start. The confirmation says so instead of forbidding it.

- [x] **Keep the mod loader up to date** (2026-11-04). `spielraum modloader`
  checks and downloads on its own — during the game start, in its own
  thread, so the network query cannot delay the start — but installs only on
  request. Enabled per game with `[modloader] quelle = "vostok"`, off by
  default because SPIELRaum touches the network nowhere else. The profile
  holds a key, not a URL. Rollback goes through the backup, not the journal
  — an installed loader should stay, crash or no crash. Background in
  [docs/modloader.md](docs/modloader.md) (German).

- [x] **Undoing only undoes our own changes now** (2026-11-03). Journal
  format 2: the journal records the old values of the keys we touched, not
  just the path of a full backup. Those values are written back into the
  *current* file; the full backup remains as a safety net underneath. Same
  for the variant path, where the backup was another five weeks older.
  Format 1 is still read — otherwise net 4 would fail for exactly the
  journals lying around right now.

  Verified against the real `Preferences.tres` of Vostok: the graphics
  values go back, while a key binding, a volume and a field of view written
  by the game all survive — with the old path all three were lost.

- [x] **Road to Vostok: movement is remapped only once now** (2026-11-03).
  Movement was remapped on both sides — keyd translated the arrow keys into
  WASD, while Vostok itself expected the arrow keys. The two cancelled each
  other out: neither the arrow keys nor WASD did anything. The game's side
  won, because it survives every reboot and does not depend on a running
  service. The profile now holds only `insert` and `delete` for reload and
  inventory — the two mappings Vostok does not offer itself.

- [x] **The permission check no longer deletes what it checks** (2026-11-03).
  `tasten._socket_erreichbar()` used `keyd bind reset` as its probe — word
  for word the command `zuruecknehmen()` uses to discard everything. Because
  the report pane calls the check on every game switch, one click in the
  game list wiped the live mapping. The check now uses `os.access` on the
  socket; the test pins down that it starts **no** subprocess.

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
