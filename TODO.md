[Deutsch](TODO.md) | [English](TODO.en.md) | [Übersicht](README.md) | [Änderungsprotokoll](CHANGELOG.md)

# TODO

Laufende Liste offener Punkte. Oben steht, was noch offen ist. Erledigtes wird
nicht gelöscht, sondern nach unten verschoben – mit dem Datum, an dem es
fertig wurde.

## Offen

- [ ] **Warum wirken MangoHuds Tastenkürzel nicht?** Angefordert am
  12.11.2026: die Anzeige im Spiel verschieben. MangoHud 0.8.4 kennt dafür
  `toggle_hud_position` und `toggle_hud`, SPIELRaum setzt beide – bei Road to
  Vostok tat sich nichts.

  Ich hatte das als erledigt gemeldet, weil die Option in
  `/usr/share/doc/mangohud/MangoHud.conf.example` steht. Nachgesehen war
  damit die Schreibweise, nicht ob sie etwas tut. Derselbe halbe Schritt wie
  bei `PROTON_USE_XALIA` am 09.11.2026.

  Was ausgeschlossen ist:

  * **Nicht die Schreibweise.** MangoHud nimmt die Zeilen ohne Klage an,
    geprüft mit `vkcube` und derselben `MANGOHUD_CONFIG`.
  * **Nicht ein fehlender Leseweg.** `libMangoHud.so` hängt an
    `libwayland-client.so.0` und `libxkbcommon.so.0` und lädt
    `libX11.so.6` bei Bedarf nach; die liegt auf diesem Rechner.

  Was noch zu prüfen wäre, in dieser Reihenfolge:

  1. Ob die Kürzel bei einem **nativen** Spiel greifen. Vostok läuft unter
     Proton und damit als XWayland-Fenster; ein natives Wayland-Spiel würde
     den anderen Weg nehmen. Das trennt »MangoHud kann nicht« von »unter
     XWayland nicht«.
  2. Ob **keyd** dazwischenkommt. Es greift das Tastaturgerät ab und schickt
     über ein eigenes; ob MangoHud das sieht, ist ungeprüft. Eine Messung mit
     zurückgenommener Belegung beantwortet es.
  3. Ob **Steam** F12 abfängt – das ist seine Taste für Aufnahmen. Betrifft
     nur `toggle_hud`, nicht das Verschieben.
  4. Ob `PROTON_ENABLE_WAYLAND=1` hilft. Das ändert den Darstellungsweg des
     ganzen Spiels und gehört deshalb hinter die anderen drei, nicht davor.

  Bis dahin verspricht SPIELRaum die Kürzel nicht mehr und nennt nur `ecke`
  im Profil. Gesetzt bleiben sie, weil sie nichts kosten.

  **Und was stattdessen gebaut werden könnte:** Die Ecke in der Oberfläche
  umschalten, statt die Profildatei zu öffnen. Wirkt erst beim nächsten
  Start, löst aber das eigentliche Anliegen – die Anzeige steht im Weg und
  soll woandershin.

- [ ] **Eine zweite Mod-Loader-Quelle einhängen.** `modloader.QUELLEN` kennt
  bisher eine, und sie zeigt auf GitHub-Veröffentlichungen. Die Form
  »Fassung aus der Datei lesen, neueste von einer Adresse holen« sollte
  tragen, ist aber nur an einem Fall erprobt. Erst am zweiten wird man
  sehen, was daran zu starr ist.

  Dabei die Warnung im Auge behalten: Dass der Vostok-Loader bei einem
  Fassungswechsel die `override.cfg` zurücksetzt, ist nur so lange harmlos,
  wie das Profil diese Datei nicht selbst anfasst. Beim Vostok-Profil ist
  das so – es fasst nur die `Preferences.tres` an. Käme dort eine
  `override.cfg`-Stellschraube hinzu, hätten wir denselben Konflikt wie bei
  den Tasten am 03.11.2026: zwei Programme, eine Datei, und keines weiß vom
  anderen.

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

  **Dasselbe gilt für fremde Programme, die sich die GPU nehmen.** Am
  04.11.2026 blieb Road to Vostok beim Start stehen, und die Ursache war
  RustDesk – ein Bildschirm, der nebenbei abgegriffen und übertragen wird,
  kostet genau die Leistung, die SPIELRaum zu messen vorgibt. Ob es bei den
  Läufen desselben Tages mitlief, lässt sich hinterher nicht mehr sagen, und
  das ist der Punkt: Eine Messung, bei der nicht feststeht, was sonst noch
  lief, ist keine.

  Mitschreiben also auch, was zur Laufzeit sonst an der Karte hing –
  Fernwartung, Bildschirmaufnahme, ein zweites Spiel. Die Namen sind kurz,
  die Liste ist über `nvidia-smi` zu haben (steht ohnehin schon in der
  Werkzeugliste), und sie beantwortet hinterher die Frage, die man sich
  sonst nicht mehr beantworten kann.

  **Zweiter belegter Fall, 12.11.2026 – und diesmal mit Zahl.** Während des
  Messlaufs nahm OBS auf. Dass es auffiel, liegt daran, dass die Aufnahme
  *mitten im Lauf* endete; derselbe Abschnitt gegen den Lauf vom 10.11.:

  ```
  Minute  2-10, OBS läuft .....  39,1 gegen 47,2     -17,3 %
  Minute 11-12, OBS aus .......  56,0 gegen 53,8      +4,1 %
  ```

  **17 Prozent** – mehr als der Abstand zwischen `optik` und `leistung` und
  mehr als alles, was in diesem Projekt je an Einstellungen gewonnen wurde.

  Und das Entscheidende: **Es steht schon in den Messdateien.** OBS kodierte
  auf dem Prozessor, die Spalte `cpu_load` zeigt es unmittelbar, die
  GPU-Last dagegen kaum. Mittel der ersten zwölf Minuten:

  ```
  optik    05.11. .... CPU 26,1 %
  leistung 09.11. .... CPU 25,7 %
  leistung 10.11. .... CPU 28,6 %
  leistung 12.11. .... CPU 68,9 %   <- Mitläufer, eindeutig
  ```

  In Minute 11 fällt die CPU-Last von 81,8 auf 38,3 Prozent und die
  Bildrate springt von 48,8 auf 57,7 – der Moment, in dem die Aufnahme
  endete, als Treppenstufe in den eigenen Daten.

  **Der kleinere Teil davon ist am 12.11.2026 gebaut** (0.9.0): Die CPU-Last
  wird pro Lauf mitgeführt und ausgegeben, und bei einem Vergleich warnt
  SPIELRaum, wenn zwei Läufe darin mehr als zehn Prozentpunkte
  auseinanderliegen. Das wirkt **rückwirkend** auf alle gespeicherten Läufe
  und hätte diesen vor der Auswertung aussortiert statt nach ihr.

  **Die zehn Prozentpunkte sind an einem Spiel kalibriert.** Bei Road to
  Vostok liegen die sauberen Läufe innerhalb von 2,9 Punkten, bei
  Enshrouded von 38,9 bis 53,0 – vierzehn Punkte, ganz ohne Mitläufer. Für
  ein prozessorhungriges Spiel ist die Schwelle also womöglich zu eng.
  Deshalb wird nur ein Paar verglichen und nicht Höchst gegen Tiefst über
  viele Läufe; sonst hätte Enshrouded bei jedem Blick gewarnt.

  Richtig wäre eine Spanne **pro Spiel**: Was bei diesem Spiel normal
  schwankt, sagen seine eigenen Läufe. Dafür braucht es mehrere saubere
  Läufe je Spiel, und die sind nur da, wo schon gemessen wurde. Bis dahin
  bleibt die Zahl eine Hausnummer, und sie steht als solche im Kommentar.

  Offen bleibt die Namensliste über `nvidia-smi`. `cpu_load` sagt, *dass* es
  jemand war – das ist die Frage, die zwischen einer Messung und keiner
  entscheidet. Wer es war, sagt es nicht. Und ein Mitläufer, der nur die
  Grafikkarte belastet und nicht den Prozessor, fällt so gar nicht auf;
  OBS fiel auf, weil es auf dem Prozessor kodierte.

  Dazu darf SPIELRaum **anzeigen**, dass Mods veraltet sind – im Befund,
  *bevor* das Spiel startet. Der Abgleich ist billig: 14 der 16 Mods nennen
  ihre Nummer, und `api.modworkshop.net/mods/versions` nimmt bis zu 100 auf
  einmal. Zwei Bedingungen: ein Schalter im Profil, **aus** als Vorgabe,
  weil SPIELRaum sonst nirgends ins Netz greift – und die Abfrage darf den
  Spielstart nie aufhalten. Ist das Netz weg, steht dort »nicht geprüft«,
  und gestartet wird wie immer.

  **Nicht** zu tun: das Herunterladen und Austauschen. Das kann der
  spielseitige Mod Loader (`modloader.gd` 3.2.1) schon selbst – Reiter
  »Updates«, Knopf »Check for Updates«, Download über
  `api.modworkshop.net`, dazu eine Selbstprüfung. Und es ist der Teil, bei
  dem etwas kaputtgeht: Er benennt beim Austauschen die Datei um
  (`_derive_updated_filename` wertet dafür die HTTP-Kopfzeilen aus), achtet
  über `priority` auf die Ladereihenfolge und verwirft seinen
  Hook-Zwischenspeicher, wenn sich eine Fassung ändert. Das nachzubauen
  heißt, sechzehn Mods aufs Spiel zu setzen, um einen Knopfdruck zu sparen.
  Derselbe Fall wie GameMode, siehe CLAUDE.md.

  Die Teilung also: SPIELRaum sagt es, der Mod Loader tut es.

  Zwei Mods kann auch er nicht prüfen, weil ihnen der `[updates]`-Abschnitt
  fehlt: *El-Prime Armor Durability* und *MedicalDurability*. Die bleiben
  Handarbeit, unabhängig davon, was gebaut wird.

- [ ] **Vergleichbar sind zwei Läufe erst, wenn dieselbe Strecke gelaufen
  wurde.** Die gleiche Messdauer ist dafür die Mindestbedingung, nicht die
  Lösung. Geprüft wird heute nur die Mindestdauer von zehn Minuten.

  **Zweimal berichtigt am 12.11.2026 – und das ist der eigentliche
  Lerninhalt.** Hier stand ab dem 10.11., die Messdauer allein koste
  6 Prozent (52,5 Bilder/s über 12,6 Minuten gegen 49,4 über 96). Dann
  stand hier das Gegenteil, gestützt auf einen dritten Lauf. Dieser dritte
  Lauf hatte aber OBS mitlaufen und ist als Messung wertlos. Beide
  Fassungen waren zu schnell geschrieben.

  Belastbar ist nur das: Innerhalb eines Laufs fällt die Zahl über die
  Länge nicht. Dieselben Läufe auf ihr eigenes Anfangsstück gekürzt, der
  Lauf mit Mitläufer weggelassen:

  ```
  Lauf                 ganz    auf 36 min    auf 12 min
  optik    05.11.      44,5        44,1          43,1
  leistung 09.11.      52,5        52,5          52,1
  leistung 10.11.      49,4        48,1          48,4
  ```

  Offen bleibt, woher der Abstand zwischen dem 09. und dem 10.11. kommt.
  Auf gleiche zwölf Minuten gekürzt bleiben 52,1 gegen 48,4, also
  7,6 Prozent – der Abstand war von Anfang an da und ist damit keine Sache
  der Dauer. Zwei Sitzungen, zwei Strecken, eine Erklärung: Das war der
  Fehler an der ersten Fassung.

  Zu tun ist also zweierlei. Das Leichte: gleiche Dauer erzwingen, oder
  auf das gemeinsame Anfangsstück kürzen – `messen.auswerten` kann das
  schon, es fehlt nur der Aufruf. Das Schwere: ein Vergleich, der die
  Strecke berücksichtigt, etwa ein festgelegter Rundweg oder Abschnitte
  gleicher GPU-Last gegeneinander. Bis dahin ist 7,6 Prozent die
  Hausnummer, unter der kein Unterschied ein Unterschied ist – was den
  Toleranzband-Punkt darunter in eine Zahl fasst.

  Und als Merkposten: Beide Fehlfassungen entstanden aus **einer**
  Messung mit einer plausiblen Erklärung daneben. Genau das ist in den
  zwei Wochen davor schon dreimal schiefgegangen. Eine Erklärung, die nur
  zu einer Messung passt, ist keine – und eine Berichtigung auf Grundlage
  einer ungeprüften Messung ist auch keine.

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

- [x] **Der Mod-Loader-Stand steht in der Oberfläche** (04.11.2026). Im
  Befund die eingebaute Fassung, ein orange hinterlegter Kasten wenn etwas
  bereitliegt, und ein Knopf, der es nach einer Rückfrage übernimmt. Gelesen
  wird nur örtlich über `stand_lokal()`; ein Test hält fest, dass der Befund
  gar nicht erst ins Netz greift – eine Abfrage beim Zeichnen würde das
  Fenster einfrieren.

  Dabei eine Annahme aus diesem TODO korrigiert: »Der Knopf darf nichts tun,
  solange das Spiel läuft – die Datei ist dann in Benutzung« stimmt unter
  Linux nicht. Geschrieben wird atomar, also daneben und dann umbenannt; das
  laufende Spiel behält seinen geöffneten Stand. Es ist nicht gefährlich,
  nur wirkungslos bis zum nächsten Start. Die Rückfrage sagt das, statt es
  zu verbieten.

- [x] **Den Mod Loader aktuell halten** (04.11.2026). `spielraum modloader`
  prüft und lädt von selbst – beim Spielstart in einem eigenen Faden, damit
  die Netzabfrage den Start nicht verzögert –, baut aber nur auf Verlangen
  ein. Eingeschaltet pro Spiel mit `[modloader] quelle = "vostok"`, Vorgabe
  aus, weil SPIELRaum sonst nirgends ins Netz greift. Im Profil steht eine
  Kennung, keine Adresse. Zurück über die Sicherung, nicht über das Journal
  – ein eingebauter Loader soll bleiben, auch nach einem Absturz.
  Hintergrund in [docs/modloader.md](docs/modloader.md).

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
