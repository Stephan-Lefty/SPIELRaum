[Deutsch](TODO.md) | [English](TODO.en.md) | [Übersicht](README.md) | [Änderungsprotokoll](CHANGELOG.md)

# TODO

Laufende Liste offener Punkte. Oben steht, was noch offen ist. Erledigtes wird
nicht gelöscht, sondern nach unten verschoben – mit dem Datum, an dem es
fertig wurde.

## Offen

- [ ] **Geführter Ablauf statt Einzelbefehle.** Gewünscht am 30.09.2026:
  Programm starten, es sucht die installierten Spiele, man klickt eines an
  und wird Schritt für Schritt durchgeführt – Ist-Zustand, Vorschlag,
  Testlauf mit Messung, Übernehmen oder Verwerfen. Am Ende startet das Spiel
  aus dem Programm heraus, und danach steht das System wieder wie vorher.

  Die Bausteine stehen inzwischen alle – `steam.spiele_finden`, `profil`,
  `zustand`, `starten`. Was fehlt, ist die Führung durch die Schritte und
  der Vergleich zweier Messungen, ohne den Schritt 4 nichts zu zeigen hat.

- [ ] **Die Umgebungsvariable für den vkd3d-proton-Zwischenspeicher
  nachschlagen.** Sie ließ sich am 30.09.2026 im Proton-Bau auf diesem
  Rechner nicht finden (weder unter `/usr/lib` noch in
  `compatibilitytools.d`). Der Zwischenspeicher liegt derzeit als
  `vkd3d-proton.cache` im Spielordner, und der liegt bei Road to Vostok auf
  einer drehenden Platte. Ihn auf die SSD umzuleiten wäre der zweite Hebel
  gegen den Flaschenhals. Quelle: die vkd3d-proton-Dokumentation, nicht das
  Gedächtnis.

- [ ] **D3D12 gegen Vulkan messen (Road to Vostok).** Das Spielprotokoll
  meldet `Driver Detected: d3d12`; Godot 4.6.2 hat Vulkan einkompiliert. Der
  Umweg über vkd3d-proton ließe sich womöglich sparen. Ob es mit den sechzehn
  Mods gutgeht, ist offen. Die Zeile steht auskommentiert im Profil.

- [ ] **.deb für Debian 13 bauen.** Ausdrücklicher Wunsch. Das Paket darf
  PySide6 später nicht aus PyPI ziehen, sondern muss die Fassung der
  Distribution nehmen. Achtung, Lehre aus MailBurg vom 14.09.2026: Ubuntu,
  Mint, Pop!_OS und Zorin führen PySide6 nicht in ihren Quellen – für die
  braucht es einen anderen Weg als das .deb.

- [ ] **Auf Debian 13 wirklich ausprobieren.** Bisher ist SPIELRaum nur auf
  Manjaro gelaufen. Die Systemerkennung ist für beide Familien gebaut, aber
  gebaut und erprobt sind zweierlei. Es hängt an einem Gerät zum Prüfen.

- [ ] **Oberfläche mit PySide6.** Erst wenn die Kommandozeile trägt. Farben
  aus [`assets/farben.md`](assets/farben.md), wie in den anderen Programmen.

- [ ] **Ein `icon.svg` zeichnen.** Alle Fassungen in `assets/` stammen aus
  einem Pixelbild. Für eine Oberfläche, die beliebig skaliert, wäre eine
  gezeichnete Form besser.

- [ ] **Prüfen, ob KDE auf Wayland überhaupt etwas zum Abschalten hat.**
  Unter X11 war »Compositor aus« ein echter Hebel. Unter Wayland gibt es das
  so nicht mehr. Was es stattdessen gibt – Tearing erlauben, VRR – ist noch
  nicht nachgesehen, nur vermutet.

## Erledigt

- [x] **Messen gebaut** (30.09.2026). `spielraum messungen` wertet die
  MangoHud-Protokolle aus und vergleicht die letzten beiden Läufe. Die ersten
  zehn Sekunden werden verworfen - sie verdoppelten im Versuch den
  Mittelwert, weil dort Shader übersetzt werden. Siehe [docs/messen.md](docs/messen.md).

- [x] **`spielraum starten` gebaut** (30.09.2026). Profil über die
  Steam-App-ID finden, Journal anlegen, Dateien mit Sicherung anpassen,
  Spiel durch `systemd-inhibit` und `gamemoderun` starten, warten,
  zurücksetzen. Signale werden an das Spiel weitergereicht, damit beim
  Abmelden nicht zu früh aufgeräumt wird.

- [x] **Zurücksetzen aus verwaisten Journalen** (30.09.2026). `spielraum
  aufraeumen` setzt jetzt wirklich zurück statt nur anzuzeigen; `--zeigen`
  behält das alte Verhalten. Der Fall steht als Test.

- [x] **Repository angelegt, Kern geprüft** (30.09.2026). Systemerkennung,
  Profilformat, Zustandsjournal und das Zusammenführen von `override.cfg`
  stehen und sind getestet. Das Zusammenführen wurde zusätzlich gegen die
  echte Datei auf der Platte gegengeprüft: Der Mod-Loader-Eintrag bleibt
  stehen.

- [x] **MangoHud und GameMode installiert** (30.09.2026). Samt der
  32-Bit-Fassungen – ohne sie greift MangoHud im Steam-Overlay nicht durch.
