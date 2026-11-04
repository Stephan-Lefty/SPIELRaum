[Deutsch](TODO.md) | [English](TODO.en.md) | [Übersicht](README.md) | [Änderungsprotokoll](CHANGELOG.md)

# TODO

Laufende Liste offener Punkte. Oben steht, was noch offen ist. Erledigtes wird
nicht gelöscht, sondern nach unten verschoben – mit dem Datum, an dem es
fertig wurde.

## Offen

- [ ] **Die Mods zur Messung mitschreiben.** Festgestellt am 03.11.2026: Die
  Messungen halten den Taktregler fest, aber nicht, welche Mods mit welcher
  Fassung liefen. Bei Road to Vostok sind das **16 Mods**, die in Inventar,
  HUD, Beleuchtung und Trefferberechnung eingreifen – die größte
  unprotokollierte Störgröße, die es hier gibt.

  Das erklärt vermutlich einen Widerspruch in den eigenen Zahlen: `optik`
  stand am 01.10.2026 bei 41,3 Bildern, am 03.11.2026 bei 48,1. Dazwischen
  haben sich die Mods geändert (ItemClarity, LM und das
  Konfigurationsmenü tragen den 21.10., ElegantHUD und die deutsche
  Übersetzung den 01.10.). Ein Vergleich über diese Grenze hinweg vergleicht
  nicht zwei Varianten, sondern zwei verschiedene Spiele. Gehört damit zum
  Toleranzband-Punkt darunter.

  Alles Nötige liegt lokal: Jede `.vmz` im `mods/`-Ordner ist ein ZIP mit
  einer `mod.txt`, darin `name`, `id` und `version`. Kein Netzzugriff.

  Bezogen werden die Mods von <https://modworkshop.net/g/roadtovostok>; die
  `mod.txt` nennt die Nummer dort als `[updates] modworkshop=<id>`.

  Zu tun: beim Messen Namen und Fassungen mitschreiben, im Befund anzeigen
  und beim Vergleich zweier Läufe warnen, wenn sie sich unterschieden haben.

  **Nicht** zu tun: das Aktualisieren der Mods. Das kann der spielseitige
  Mod Loader (`modloader.gd` 3.2.1) schon selbst – Reiter »Updates«, Knopf
  »Check for Updates«, Herunterladen über `api.modworkshop.net`, dazu eine
  Selbstprüfung. Derselbe Fall wie GameMode, siehe CLAUDE.md. Nur zwei Mods
  kann auch er nicht prüfen, weil ihnen der `[updates]`-Abschnitt fehlt:
  *El-Prime Armor Durability* und *MedicalDurability*.

- [ ] **Die Messfahrt braucht ein Toleranzband.** `fahrt.beste()` nimmt
  schlicht das höchste 1-%-Tief und erklärt damit einen Sieger, auch wenn
  der Abstand Rauschen ist. Am 03.11.2026 lagen `optik` (26,54) und
  `leistung` (26,31) 0,9 % auseinander – empfohlen wurde `optik`, obwohl
  `leistung` bei gleicher Ruhe 12 % mehr Bilder lieferte und dabei 56 %
  länger gemessen wurde (lange Läufe fallen niedriger aus). Nach dem
  eigenen Maßstab des Projekts ist das keine Entscheidung, sondern Rauschen
  mit Nachkommastelle.

  Nötig ist eine Schwelle, unterhalb derer SPIELRaum »kein Unterschied«
  sagt und dann nach dem Mittelwert aufschlüsselt – oder gar keine
  Empfehlung abgibt und nur die Zahlen zeigt. Die Schwelle muss aus den
  Messdaten begründet sein, nicht geschätzt.

  Dazu gehört auch: `ausgangszustand` in der Fahrtenakte stand am
  03.11.2026 auf `null`, obwohl `--abbrechen` damit den Ausgangszustand
  wiederherstellen soll.

- [ ] **Übersicht der Tastenbelegung aus dem Profil erzeugen.** Am 23.10.2026
  entstanden zwei PDFs aus Wegwerfskripten – und waren fünf Minuten später
  veraltet, weil die Belegung sich geändert hatte. Ein Befehl
  `spielraum tasten <spiel>` sollte sie aus Profil und Spieldatei bauen.
  Wichtig dabei: Es muss die *gedrückte* Taste zeigen, nicht die, die im
  Spielmenü steht – seit keyd dazwischensitzt, sind das zwei verschiedene.

- [ ] **Schnellzugriff ohne Ziffernblock.** Die SKILLER SGK50 S3 hat keinen.
  Damit sind die Zahlen 1 bis 7 unerreichbar, auf denen in fast jedem Spiel
  der Schnellzugriff liegt. Das Raster I/O/P – K/L/Ö – M/,/. entspräche
  räumlich einem Ziffernblock, kostet aber die Buchstaben selbst. Nicht
  ausprobiert.

- [ ] **Bildraten belastbar vergleichbar machen.** Am 01.10.2026 gemessen:
  Innerhalb *eines* Laufs schwankte die Bildrate von 30,9 auf 53,8 – 74 %,
  allein durch die Stelle im Spiel. Der Unterschied zwischen Festplatte und
  SSD betrug 16 %, der zwischen D3D12 und Vulkan 0,6 %. Die Störgröße ist
  also größer als alles, was gemessen werden sollte.

  Ladezeiten misst SPIELRaum zuverlässig, Bildraten nur grob. Siehe
  [docs/messen.md](docs/messen.md). Denkbare Wege: über viele Läufe die
  Verteilung zeigen statt einzelner Mittelwerte; Abschnitte gleicher
  GPU-Last gegeneinander halten; Spiele mit eingebautem Messlauf gesondert
  behandeln.

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
  `vkd3d-proton.cache` im Spielordner. Seit dem Umzug auf die SSD weniger
  dringend, und für Road to Vostok gegenstandslos – das Spiel fährt Vulkan
  direkt, vkd3d-proton ist raus. Für andere Spiele bleibt es gültig. Quelle:
  die vkd3d-proton-Dokumentation, nicht das Gedächtnis.

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

- [ ] **Node.js 20 in den Actions.** GitHub meldet seit dem ersten Lauf am
  30.09.2026: `actions/checkout@v4` und `actions/setup-python@v5` zielen auf
  Node.js 20 und werden übergangsweise auf 24 gezwungen. Läuft noch, bricht
  irgendwann. Betrifft alle Repositorien gleichermaßen – besser in einem Zug
  erledigen als einzeln.

- [ ] **Prüfen, ob KDE auf Wayland überhaupt etwas zum Abschalten hat.**
  Unter X11 war »Compositor aus« ein echter Hebel. Unter Wayland gibt es das
  so nicht mehr. Was es stattdessen gibt – Tearing erlauben, VRR – ist noch
  nicht nachgesehen, nur vermutet.

## Erledigt

- [x] **Zurücksetzen nimmt nur noch die eigenen Änderungen zurück**
  (03.11.2026). Journalfassung 2: Im Journal stehen die alten Werte der
  angefassten Schlüssel, nicht nur der Pfad einer Vollsicherung.
  Zurückgeschrieben wird in die *aktuelle* Datei, die Vollsicherung bleibt
  als Netz darunter. Dasselbe im Variantenweg, wo die Sicherung noch fünf
  Wochen älter war. Fassung 1 wird weiter gelesen, sonst fiele Netz 4 für
  die Journale aus, die gerade herumliegen.

  Gegengeprobt an der echten `Preferences.tres` von Vostok: Grafikwerte
  gehen zurück, eine vom Spiel geschriebene Tastenbelegung, Lautstärke und
  Blickfeld bleiben stehen – mit dem alten Weg waren alle drei weg.

- [x] **Road to Vostok: Bewegung wird nur noch einmal umgelegt**
  (03.11.2026). Die Bewegung lag auf beiden Seiten – keyd übersetzte die
  Pfeiltasten nach WASD, und Vostok erwartete selbst die Pfeiltasten. Beides
  hob sich auf: Weder Pfeiltasten noch WASD taten etwas. Entschieden wurde
  für die Seite des Spiels, weil sie jeden Neustart überlebt und nicht an
  einem laufenden Dienst hängt. Im Profil stehen nur noch `insert` und
  `delete` für Nachladen und Inventar – die beiden Zuordnungen, die Vostok
  selbst nicht anbietet.

- [x] **Die Rechteprüfung löscht nicht mehr, was sie prüft** (03.11.2026).
  `tasten._socket_erreichbar()` benutzte `keyd bind reset` als Testaufruf –
  wortgleich der Befehl, mit dem `zuruecknehmen()` alles verwirft. Weil der
  Befund im Fenster die Prüfung bei jedem Spielwechsel aufruft, löschte ein
  Klick in die Spieleliste die laufende Belegung. Geprüft wird jetzt mit
  `os.access` auf dem Socket; der Test fixiert, dass die Prüfung **keinen**
  Unterprozess startet.

- [x] **Messfahrt gebaut.** 23.10.2026. Fahrtenakte unter
  `~/.local/share/spielraum/fahrten/`, Unterbefehl `messfahrt`, Knopf in
  der Oberfläche. Offen geblieben ist die Prüfung, ob die Einstellungen
  während des Laufs unverändert blieben – Begründung in
  [docs/messfahrt.md](docs/messfahrt.md).

- [x] **D3D12 gegen Vulkan gemessen** (30.09.2026). Ergebnis: **kein
  Unterschied** - 49,0 gegen 49,3 Bilder/s ist Rauschen. Die Vermutung, der
  Umweg über vkd3d-proton koste Leistung, ist damit für dieses Spiel auf
  dieser Karte widerlegt. Vulkan bleibt trotzdem eingeschaltet; es kostet
  auch nichts.

- [x] **Road to Vostok auf die SSD umgezogen** (30.09.2026). Der Befund, der
  sich in beiden Läufen hielt: 24 bis 25 Sekunden Ladezeit und Aussetzer
  beim Nachladen. Gemessen wurde dann die Platte selbst - 112 MB/s und
  7,76 ms je Sprung gegen 509 MB/s und 0,13 ms auf der SSD. **Nachgemessen
  am 01.10.2026: Ladezeit von 23,8 auf 6,6 Sekunden.** Die Vorhersage lautete
  6 bis 9 Sekunden. Bildrate und Aussetzer blieben dagegen unverändert –
  entgegen der Vorhersage, siehe den Punkt zur Messbarkeit oben.

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
