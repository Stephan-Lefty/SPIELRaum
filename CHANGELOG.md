[Deutsch](CHANGELOG.md) | [Übersicht](README.md) | [TODO](TODO.md)

# Änderungsprotokoll

Alle nennenswerten Änderungen an SPIELRaum stehen hier.

Das Format folgt [Keep a Changelog](https://keepachangelog.com/de/1.1.0/),
die Versionsnummern folgen [Semantic Versioning](https://semver.org/lang/de/).

## [0.9.0] – 2026-11-12

### Hinzugefügt

- **Die CPU-Last jedes Laufs wird mitgeführt – und gemeldet, wenn zwei
  Läufe darin weit auseinanderliegen.** Sie steht in `spielraum messungen`,
  in der Befundtafel, in der Fahrtenakte und in der Tabelle am Ende einer
  Messfahrt. Weichen zwei verglichene Läufe um mehr als zehn
  Prozentpunkte ab, sagt SPIELRaum, dass der Vergleich nichts taugt.

  Der Anlass: Am 12.11.2026 nahm OBS während eines Messlaufs von Road to
  Vostok auf und kodierte dabei auf dem Prozessor. Aufgefallen ist es nur,
  weil die Aufnahme mitten im Lauf endete – danach sprang die Bildrate von
  48,8 auf 57,7 Bilder/s. Gegen denselben Streckenabschnitt zwei Tage
  davor gerechnet, kostete die Aufnahme **17 Prozent**: mehr, als in
  diesem Projekt je eine Einstellung gebracht hat.

  Und es stand die ganze Zeit in der Messdatei, Spalte `cpu_load` – 26 bis
  29 Prozent in den sauberen Läufen gegen 69 in diesem. Niemand hat
  hingesehen, und zwei falsche Schlüsse landeten im Repo, bevor es
  auffiel. Was sich aus den eigenen Daten ablesen lässt, soll nicht am
  Hinsehen hängen.

  SPIELRaum sagt es und verwirft nichts von selbst: Es kann der Mitläufer
  gewesen sein, es kann auch die Stelle im Spiel gewesen sein. Welches von
  beidem, weiß das Protokoll nicht.

  Die Prüfung wirkt **rückwirkend** auf alle gespeicherten Läufe – die
  Spalte schreibt MangoHud ohnehin mit. Fehlt sie, fällt nur diese eine
  Prüfung aus; eine Messung bleibt es trotzdem.

  Gewarnt wird über die beiden **jüngsten** Läufe, nicht über die Spanne
  aller gezeigten. Die erste Fassung nahm Höchst gegen Tiefst über sechs
  Läufe und warnte damit bei Enshrouded bei jedem Blick: Dessen saubere
  Läufe liegen von 38,9 bis 53,0 Prozent auseinander, bei Road to Vostok
  sind es 2,9. Eine Warnung, die immer kommt, liest nach der dritten
  niemand mehr. Die CPU-Last der älteren Läufe steht weiter in der
  Tabelle – sichtbar bleibt sie, behauptet wird nur nichts über sie.

  Gewarnt wird erst ab einer Minute gemessener Spielzeit. Ohne diese Grenze
  stützte sich die Warnung beim ersten Nachsehen auf einen Lauf von
  **13 Sekunden** und meldete 42 Prozentpunkte Unterschied, wo in den
  brauchbaren Läufen 32 lagen – also genau der Fehler, den sie verhindern
  soll: eine Zahl aus zu wenig Material. Die CPU-Last wird für kurze Läufe
  weiter ausgewiesen, nur verglichen wird sie nicht.

- **Die Anzeige lässt sich in der Oberfläche umstellen** – wo sie sitzt und
  wie viel sie zeigt. Zwei Felder unten rechts neben »Anzeige:«; sie
  schreiben `ecke` und `umfang` in die Profildatei und wirken beim nächsten
  Spielstart, was auch in der Rückmeldung dabeisteht.

  Der Ersatz für MangoHuds Tastenkürzel, die hier nicht wirken.

  Geschrieben wird **eine Zeile im Text**, nicht die Datei neu serialisiert.
  Die Profile hier bestehen zu neun Zehnteln aus Begründung – das
  Vostok-Profil hat 320 Kommentarzeichen auf 377 Zeilen –, und kein
  TOML-Schreiber in der Standardbibliothek erhält Kommentare. Wer neu
  serialisiert, löscht die Begründungen und merkt es nicht, weil die Datei
  danach gültig aussieht: dieselbe Falle wie bei der Vollsicherung am
  03.11.2026.

  Die drei Umfänge heißen »alles«, »nur Bilder/s« und **»nichts – misst dann
  auch nicht«**. Der Zusatz ist keine Floskel, sondern gemessen am
  12.11.2026 mit `vkcube`, zwei Durchgänge je Einstellung:

  ```
  voll ............ 55 protokollierte Zeilen
  nur Bilder/s .... 55 bis 60 Zeilen
  aus .............  0 Zeilen
  ```

  MangoHuds `no_display` hält auch das Mitschreiben an. Wer die Anzeige
  wegnimmt, verliert die Messung mit – und erführe es sonst nie, weil ein
  Lauf ohne Protokoll genauso aussieht wie einer, der nie stattgefunden hat.
  Deshalb steht die Folge im Auswahltext selbst, und im Befund dann »es wird
  nicht gemessen« statt »jeder Lauf wird gemessen«. Wer nur weniger im Bild
  will, nimmt »nur Bilder/s« – MangoHuds `fps_only`, Messung läuft weiter.

  Dass hier gemessen statt angenommen wurde, ist die Lehre aus den
  Tastenkürzeln vom selben Tag: Dort war die Option nachgesehen und die
  Wirkung geraten.

  Die Rückmeldung steht in der Unterzeile, nicht in einem Dialog. Wer die
  sechs Stellen durchprobiert, klickt sonst sechsmal etwas weg.

  Drei Fehler dabei gefunden und behoben, alle von Tests: Mit einem
  Kommentar hinter dem Wert gab die Schreibfunktion den falschen alten Wert
  zurück. `read_text` wandelt CRLF beim **Lesen** in LF – derselbe Fehler
  wie am 09.11.2026 an Enshroudeds Einstellungsdatei, nur am anderen Ende.
  Und `currentIndexChanged` feuert auch beim **Befüllen** des Feldes, womit
  jeder Blick auf ein Spiel in dessen Profil geschrieben hätte: dieselbe
  Falle wie bei `currentRowChanged` am 09.11.2026, nur in die andere
  Richtung.

- **Ein Knopf zu den Aufnahmen aus dem Spiel.** Rechts neben »Mod Loader
  einbauen«, mit der Anzahl darauf. Steam legt die Bilder unter
  `userdata/<Konto>/760/remote/<App-ID>/screenshots` ab -- eine Stelle, die
  niemand errät. Der Knopf ersetzt also keine Funktion, er erspart das
  Suchen.

  Er bleibt grau, wenn keine Aufnahme vorliegt: Steam legt den Ordner schon
  beim ersten Spielstart an, »Ordner vorhanden« ist deshalb kein Grund, den
  Knopf freizugeben. Geöffnet wird über den Schreibtisch, nicht über einen
  festen Programmnamen -- unter KDE ist es Dolphin, unter GNOME Nautilus.

  Mehrere Steam-Konten auf einem Rechner geben mehrere Ordner; dann gehen
  alle auf, statt dass SPIELRaum sich für eines entscheidet.

- **`messen.deckkraft` im Profil, und die Anzeige lässt sich im Spiel
  verschieben.** Der Kasten hinter den Zahlen ist jetzt zu einem Viertel
  deckend statt zu MangoHuds Hälfte; `deckkraft = 0` lässt ihn ganz weg.
  Die Schrift bleibt voll deckend – durchsichtige Zahlen vor einem hellen
  Himmel kann man nicht lesen.

  **Verschoben wird über `ecke` im Profil, nicht im laufenden Spiel.** Hier
  stand zuerst, `Shift rechts + F11` schalte eine Stelle weiter. MangoHud
  kennt die Option und SPIELRaum setzt sie auch – sie wirkte bei Road to
  Vostok aber nicht. Nachgesehen war die Schreibweise, nicht ob sie etwas
  tut; derselbe halbe Schritt wie bei `PROTON_USE_XALIA` am 09.11.2026.

  Nicht die Ursache: die Schreibweise (MangoHud nimmt die Zeilen ohne Klage
  an, geprüft mit `vkcube`) und fehlende Lesewege (die Bibliothek hängt an
  `libwayland-client` und `libxkbcommon` und lädt `libX11.so.6` nach, die
  vorhanden ist). Woran es liegt, ist offen und steht in TODO.md. Die
  Kürzel bleiben gesetzt – sie kosten nichts –, versprochen werden sie
  nicht.

### Geändert

- **Die Fahrtenakte steht auf Fassung 2.** Eine Akte aus Fassung 1 wird
  weiter gelesen und beim nächsten Schreiben fortgeschrieben – ihr fehlt
  nur ein Feld, sie hat keinen anderen Aufbau. Sie wegzuwerfen hieße, eine
  fertig gemessene Fahrt zu verlieren, weil eine Spalte dazugekommen ist.
  Dieselbe Entscheidung wie beim Zustandsjournal.

  Dabei behoben: Eine Akte mit einem unbekannten Feld löste bisher mitten
  im Spielstart einen `TypeError` aus. Unbekannte Felder werden jetzt
  weggefiltert.

## [0.8.5] – 2026-11-09

### Behoben

- **Ein Klick auf das bereits gewählte Spiel liest jetzt neu.** Die Liste
  hing nur an `currentRowChanged`, und das feuert ausschließlich bei einem
  Zeilen*wechsel*. Wer auf das ohnehin ausgewählte Spiel klickte, um den
  Befund aufzufrischen, bekam nichts – der Mod-Loader-Knopf blieb grau,
  obwohl im Zwischenlager längst die Fassung 3.5.0 lag. Nur »Neu einlesen«
  half, weil das Leeren der Liste einen Zeilenwechsel erzwingt.

  Der Befund ist bewusst eine Momentaufnahme und fragt von sich aus nichts
  nach – genau deshalb friert das Fenster nie ein. Dann muss aber der
  naheliegende Griff, noch einmal draufzuklicken, auch wirken.

## [0.8.4] – 2026-11-05

### Behoben

- **Das Tastenblatt wurde im Befund selbst geöffnet statt im PDF-Programm.**
  Ein Klick auf »Tastenblatt öffnen« füllte das rechte Feld mit
  `%PDF-1.4 ReportLab Generated PDF document…` – dem Rohtext der Datei.

  `setOpenExternalLinks(True)` allein genügt nicht: Ein QTextBrowser hält
  eine `file://`-Adresse für ein Dokument, das er selbst anzeigen kann.
  Jetzt verfolgt er Verweise gar nicht mehr (`setOpenLinks(False)`) und
  meldet den Klick nur; geöffnet wird über `QDesktopServices`, also mit
  dem Programm, das der Anwender dafür eingerichtet hat.

- **Leerzeichen im Pfad machten die Adresse ungültig.** Der Verweis wurde
  von Hand als `file://{pfad}` zusammengesetzt. Liegt das Repository unter
  »/mnt/raid/eigene Daten/…«, ist das keine gültige Adresse. Jetzt über
  `QUrl.fromLocalFile`, und zwar mit `FullyEncoded` – die Vorgabe von
  `toString()` dekodiert das Leerzeichen wieder, womit nichts gewonnen
  wäre. Genau das hat der Test beim ersten Lauf gefangen.

## [0.8.3] – 2026-11-05

### Behoben

- **`messen.fahrt_varianten` gilt jetzt auf allen drei Wegen in eine
  Messfahrt.** Bisher wertete nur die automatisch begonnene Fahrt den
  Profileintrag aus; `spielraum messfahrt --starten` und der Knopf in der
  Oberfläche nahmen stumm **alle** Varianten.

  Aufgefallen am 05.11.2026: Im Profil von Road to Vostok stehen zwei
  Varianten, angekündigt wurden vier Läufe zu je zehn Minuten – vierzig
  Minuten Spielzeit statt zwanzig, ohne dass jemand danach gefragt hätte.
  Im Änderungsprotokoll zu 0.6.1 steht die Einschränkung ohne Vorbehalt;
  sie galt nur auf einem von drei Wegen.

  Die Antwort auf »welche Varianten misst eine Fahrt« steht jetzt an einer
  Stelle: `Profil.mess_varianten()`. Jeder der drei Wege hat dazu einen
  eigenen Test – der Fehler bestand gerade darin, dass dieselbe Frage
  dreimal verschieden beantwortet wurde. `--nur` sticht die Profilauswahl
  weiterhin für den einen Aufruf.

## 0.8.2 – 2026-11-05

### Geändert

- Das Programm erscheint jetzt in der Software-Verwaltung (GNOME
  Software, KDE Discover, Cinnamons Anwendungsverwaltung) - mit
  Beschreibung und zum Entfernen auf Knopfdruck. Dafür fehlten bisher
  die AppStream-Angaben; ohne sie kennen die Verwaltungen ein Programm
  schlicht nicht.

## [0.8.1] – 2026-11-04

### Hinzugefügt

- **Der Mod-Loader-Stand steht in der Oberfläche.** Im Befund die
  eingebaute Fassung; liegt eine neuere heruntergeladen bereit, ein orange
  hinterlegter Kasten und der Knopf **»Mod Loader 3.4.2 einbauen«**. Er
  fragt vorher nach und nennt beide Fassungen, den Weg zurück und die
  längere Ladezeit beim nächsten Start. Liegt nichts bereit, ist er grau.

  Gelesen wird nur örtlich (`stand_lokal`): installierte Fassung und
  Zwischenlager. Ein Test hält fest, dass der Befund **gar nicht erst** ins
  Netz greift – eine Abfrage beim Zeichnen würde das Fenster einfrieren,
  bis die Antwort da ist, und bei abgelehnter Verbindung bis zur
  Zeitgrenze.

  Dort steht deshalb auch nie »aktuell«: Geprüft wird beim Spielstart, und
  wer lange nicht gespielt hat, hat lange nicht geprüft.

### Berichtigt

- **Einbauen bei laufendem Spiel ist nicht gefährlich**, anders als vorher
  notiert. Geschrieben wird atomar – daneben, dann umbenennen –, das
  laufende Spiel behält seinen geöffneten Stand. Es ist nur wirkungslos bis
  zum nächsten Start, und die Rückfrage sagt das.

## [0.8.0] – 2026-11-04

### Hinzugefügt

- **`spielraum modloader` hält den Mod Loader aktuell.** Der Vostok Mod
  Loader aktualisiert *die Mods* selbst, sich selbst aber nicht – er prüft
  nur und bietet »Open Page« an, das einen Browser öffnet. Auf diesem
  Rechner lief deshalb am 04.11.2026 die Fassung 3.2.1, während seit dem
  06.10.2026 v3.4.2 veröffentlicht war.

  **Geprüft und heruntergeladen wird von selbst**, beim Spielstart in einem
  eigenen Faden, damit die Netzabfrage den Start nicht um ihre Laufzeit
  verzögert. Ohne Netz steht »nicht geprüft« und gestartet wird wie immer.

  **Eingebaut wird nur auf Verlangen** (`--einbauen`). Grund: Bei einem
  Fassungswechsel verwirft der Loader seinen Hook-Zwischenspeicher, löscht
  seinen Zustand und setzt die `override.cfg` zurück – eine neue Fassung
  kann das Zusammenspiel mit den installierten Mods verändern, und das soll
  niemanden in der Sekunde überraschen, in der er spielen wollte. Zurück
  geht es mit `--zurueck`; die alte Fassung wird vorher gesichert.

  Eingebaut wird nur, was sich ausweisen kann: über 50 KB groß, mit
  Fassungszeile, und diese muss zu der Marke passen, die GitHub nennt.
  Sonst wird nichts angefasst und gesagt, was nicht stimmte.

  Angeschaltet wird pro Spiel mit `[modloader] quelle = "vostok"`. Vorgabe
  aus, weil SPIELRaum sonst nirgends ins Netz greift. Im Profil steht eine
  **Kennung**, keine Adresse – eine URL in einer Datei, die jeder
  bearbeiten kann, wäre ein Weg ins Spielverzeichnis.

  Siehe [docs/modloader.md](docs/modloader.md).

- **`spielraum pruefen` nennt Tastenbelegung und Mod Loader**, damit
  sichtbar ist, was an einem Profil überhaupt eingeschaltet ist.

### Nicht gebaut

- **Das Aktualisieren der Mods selbst.** Das kann der Mod Loader, samt
  Umbenennen beim Austauschen, Ladereihenfolge über `priority` und dem
  Verwerfen des Hook-Zwischenspeichers. Nachbauen hieße, sechzehn Mods aufs
  Spiel zu setzen, um einen Knopfdruck zu sparen.

## [0.7.0] – 2026-11-03

### Geändert

- **Zurücksetzen nimmt nur noch die eigenen Änderungen zurück.** Das ist
  der Umbau am Kernversprechen des Programms. Angewendet wurde immer
  chirurgisch – nur die Schlüssel, die im Profil stehen. Zurückgesetzt
  wurde dagegen mit der ganzen Sicherung, und damit verschwand alles, was
  das Spiel während des Laufs selbst in dieselbe Datei geschrieben hatte.

  Bei Road to Vostok stehen in der `Preferences.tres` neben den
  Grafikeinstellungen die **Tastenbelegung**, die Lautstärken und das
  Blickfeld. Jeder Lauf holte denselben Stand zurück: Die Sicherung vom
  01.10.2026 und alle fünf vom 03.11.2026 waren byte-identisch. Die Datei
  konnte sich fünf Wochen lang nicht ändern, und eine Umbelegung im
  Spielmenü war mit dem nächsten Spielende wieder weg.

  Im Journal stehen jetzt die alten Werte der angefassten Schlüssel, als
  Text und damit typgetreu (`1.0` bleibt `1.0`). Zurückgesetzt wird in die
  *aktuelle* Datei. Die Vollsicherung bleibt als Netz darunter, nicht als
  Weg. Gleiches gilt für `spielraum variante --zurueck`, wo dieselbe
  Sicherung noch fünf Wochen älter war.

- **Journalfassung 2.** Fassung 1 wird weiter gelesen und über den alten
  Weg aufgelöst – sonst räumte eine neue Fassung nicht hinter der vorigen
  auf, und Netz 4 fiele für genau die Journale aus, die noch herumliegen.

- **Einstellungsdateien werden atomar geschrieben** (daneben, dann
  umbenennen) – dasselbe Verfahren wie beim Journal. Eine halb geschriebene
  `.tres` mit Tastenbelegungen darin sieht gültig aus.

### Behoben

- **Ein Schlüssel, den SPIELRaum selbst angelegt hat, wird beim
  Zurücksetzen wieder entfernt** statt auf einen alten Wert gesetzt, den es
  nie gab. Dazu können `godot_cfg` jetzt auch Zeilen und Abschnitte
  entfernen.

- **`godot_cfg` verlor beim Umbauen eine leere Schlusszeile.** `splitlines()`
  plus »Zeilenumbruch anhängen« ist nicht verlustfrei. Fiel erst auf, als das
  Zurücksetzen überhaupt durch diesen Code lief – vorher wurde die Datei ja
  zurückkopiert.

## [0.6.2] – 2026-11-03

### Behoben

- **Die Rechteprüfung löschte die Tastenbelegung, die sie prüfte.**
  `tasten._socket_erreichbar()` probierte den Socket-Zugriff mit
  `keyd bind reset` aus – wortgleich der Befehl, mit dem
  `zuruecknehmen()` jede gesetzte Belegung verwirft. Weil der Befund im
  Fenster die Prüfung bei jedem Spielwechsel aufruft, löschte ein Klick in
  die Spieleliste die laufende Belegung. Geprüft wird jetzt mit
  `os.access` auf `/run/keyd.socket`; ein Test hält fest, dass die Prüfung
  keinen Unterprozess mehr startet.

### Geändert

- **Road to Vostok legt die Bewegung selbst um, nicht keyd.** Die Bewegung
  lag auf beiden Seiten und hob sich auf – weder Pfeiltasten noch WASD taten
  etwas. Im Profil stehen nur noch `insert` und `delete`.

### Bekannt

- **Zurücksetzen nimmt mehr zurück als die eigenen Änderungen.** Angewendet
  wird chirurgisch, zurückgesetzt wird die ganze Datei. Was das Spiel selbst
  hineinschreibt – bei Vostok Tastenbelegung, Lautstärken, Blickfeld –, ist
  beim Beenden weg. Beschrieben in [TODO.md](TODO.md); bis zur Behebung
  gehören Einstellungen ins Profil, nicht ins Spielmenü.

## [0.6.1] – 2026-10-23

### Hinzugefügt

- **`[messen] fahrt = true`** beginnt die Messfahrt beim nächsten
  Spielstart von selbst. Vorgabe aus: Eine Messfahrt verstellt die
  Grafikeinstellungen, und das soll niemanden überraschen, der nur spielen
  will.

- **`[messen] fahrt_varianten`** schränkt ein, was die Messfahrt misst.
  Ohne die Zeile sind es alle – und vier Varianten bedeuten drei
  Viertelstunden Spielzeit.

- **Eine abgeschlossene Fahrt bleibt liegen** statt gelöscht zu werden –
  als Ergebnisspeicher und als Merker. Ohne das begänne bei eingeschalteter
  Automatik nach jedem Verwerfen sofort die nächste Fahrt.

## [0.6.0] – 2026-10-23

Die Messfahrt. Entworfen am 01.10.2026, jetzt gebaut.

### Hinzugefügt

- **`spielraum messfahrt`** und ein Knopf in der Oberfläche. Drei Läufe zu
  je zehn Minuten, dazwischen stellt SPIELRaum selbst um. Am Ende eine
  Tabelle und die Möglichkeit, eine Variante zu übernehmen.

- **Die Fahrtenakte** (`spielraum/fahrt.py`). SPIELRaum läuft nicht
  durchgehend – zwischen zwei Läufen existiert kein Prozess, der sich etwas
  merken könnte. Die Akte liegt deshalb auf der Platte, atomar geschrieben,
  und überlebt auch einen Neustart.

- **Der Ausgangszustand steht in der Akte**, nicht nur im Journal. Bricht
  jemand nach dem zweiten Lauf ab, kennt das Journal des zweiten Laufs nur
  den Zustand von Lauf eins.

- **Zu kurze Läufe zählen nicht** und werden wiederholt, mit Begründung.
  Die Mindestdauer von zehn Minuten folgt aus einer Messung: Fünf Minuten
  ergaben 60,6 Bilder/s, vierzig Minuten 46,1 – bei identischen
  Einstellungen.

- **Bewertet wird nach dem 1-%-Tiefstwert**, nicht nach dem Mittel. Der
  Mittelwert sagt, wie es im Schnitt aussah; der Tiefstwert sagt, wie
  schlecht es in den schlechtesten Momenten wurde – und die nimmt man als
  Ruckeln wahr.

- **Liegende Fahrten meldet `spielraum aufraeumen`.** Wer nach drei Wochen
  wieder spielt, erinnert sich nicht an eine halb gelaufene Messfahrt.

### Wissenswert

- **Die Umhüllung führt nicht.** Sie setzt, was in der Akte steht, misst und
  schreibt zurück – sie startet insbesondere kein Spiel neu. Wer nach dem
  ersten Lauf keine Lust mehr hat, soll nicht gegen ein Spiel ankämpfen, das
  sich von selbst wieder öffnet.

## [0.5.1] – 2026-10-23

### Hinzugefügt

- **`werkzeuge/tastenblatt.py`** erzeugt eine Übersicht aus Profil und
  Spieldatei – mit der Taste, die *gedrückt* wird, nicht der, die im
  Spielmenü steht. Seit keyd dazwischensitzt, sind das zwei verschiedene
  Dinge.

- **Die Oberfläche zeigt die Tastenbelegung** des gewählten Spiels und
  verweist auf das Blatt, falls eines unter `tastenblaetter/` liegt. Der
  Ordner wird von Git ignoriert: Eine Belegung hängt an der Hand, die die
  Maus führt.

- **Das Messfenster zeigt mehr als die Bildrate.** Bisher setzte SPIELRaum
  nur `MANGOHUD=1`, und MangoHud zeigte eine nackte Zahl. Jetzt stehen dort
  GPU-Temperatur, Drosselstatus, Grafikspeicher und ein Verlaufsgraph – die
  Auswahl folgt dem, was bei Enshrouded den Unterschied machte.

- **Spiele ohne Profil werden trotzdem gemessen.** Sonst entsteht nie ein
  Profil, weil die Grundlage dafür fehlt. Die Messung ist dabei der einzige
  Eingriff.

- **Tastenbelegung für Road to Vostok.** Dafür musste die Spielbelegung auf
  die Vorgabewerte zurück; drei Aktionen (`item_drop`, `prepare`,
  `rail_movement`) lagen auf Umschalt und Strg und mussten auf L, O und P
  ausweichen.

### Behoben

- **Die CI war seit dem 01.10.2026 rot**, ohne dass es auffiel: `libEGL`
  fehlte im Runner, pytest meldete »85 passed, 3 errors«, und eine Zeile,
  die mit »85 passed« anfängt, liest sich wie ein grüner Lauf.

## [0.5.0] – 2026-10-23

Tastenbelegung pro Spiel. Für alle, die die Maus links führen und mit der
rechten Hand nur den Bereich ab I/K/M erreichen – während Spiele ihre
Befehle auf WASD und die linke Umschalttaste legen.

### Hinzugefügt

- **`[tasten]` im Profil** und **`spielraum/tasten.py`**. Links steht, was
  gedrückt wird, rechts, was das Spiel sehen soll. Gesetzt wird beim
  Spielstart über `keyd`, zurückgenommen beim Beenden – mit Journaleintrag,
  also auch dann, wenn SPIELRaum dazwischen abstürzt.

- **Ohne root und ohne Polkit.** keyd legt einen Socket an, der der Gruppe
  `keyd` gehört. Wer darin ist, darf dem Dienst Belegungen schicken.
  SPIELRaum selbst braucht keine erhöhten Rechte – anders als bei GameMode,
  wo die Polkit-Regel des Manjaro-Pakets auf `allow_active=no` steht und
  deshalb nichts ausrichtet.

- **Ein Knopf in der Oberfläche**, der die Belegung von Hand setzt und
  zurücknimmt. Für den Fall, dass ein Spiel direkt über Steam gestartet wird.

- **Profil für Enshrouded** (`profile/1203620-enshrouded.toml`). Bewusst ohne
  Grafikeinstellungen: Gemessen ist bisher nur, was die Grafikkarte tut.

- **[docs/tasten.md](docs/tasten.md)** mit dem Einrichtungsweg und den beiden
  Fallen, die am 23.10.2026 Zeit gekostet haben.

### Wissenswert

- **Die Belegung gilt nur, solange das Spiel läuft.** Erst stand sie fest in
  `/etc/keyd/`. Dann schrieb die Pfeiltaste auch im Browser ein »w«. Eine
  Übersetzung, die immer gilt, ist keine Spieleinstellung, sondern ein neues
  Tastaturlayout.

- **Die Spielbelegung muss auf den Vorgabewerten stehen.** Übersetzt sowohl
  die Tastatur als auch das Spiel, heben sich beide auf. Bei Enshrouded löste
  *Ende* dadurch Ausweichen statt Schleichen aus und *Entf* das Baumenü statt
  des Rucksacks – gefunden hat das erst eine Gegenprobe, die jede gesendete
  Taste gegen die Spielbelegung hält.

- **keyd versteht keine Kommentare am Zeilenende.** Es verwirft solche Zeilen
  mit einer bloßen Warnung statt mit einem Abbruch. Sechs Belegungen waren
  still verschwunden, bis `keyd check` es meldete.

## [0.3.0] – 2026-09-30

Gemessen wird jetzt. Damit ist SPIELRaum kein Programm mehr, das Einstellungen
verstellt und behauptet, es sei besser geworden.

### Hinzugefügt

- **`spielraum messungen`** (`spielraum/messen.py`). Wertet die
  MangoHud-Protokolle aus und stellt die letzten beiden Läufe gegenüber.

- **Die ersten zehn Sekunden zählen nicht.** Das ist die wichtigste
  Entscheidung in diesem Modul, und sie ist nachgemessen. An einem
  zwanzigsekündigen Lauf:

      Mittel ab 10 s:        102,3 Bilder/s
      Mittel ganzer Lauf:     50,8 Bilder/s

  Der Mittelwert **verdoppelt sich**, sobald die Aufwärmphase draußen ist.
  Dort übersetzt das Spiel Shader und lädt nach; wer das mitrechnet, misst
  die Ladezeit. Die Tiefstwerte bleiben dagegen fast gleich – die Ruckler
  verteilen sich über den ganzen Lauf.

- **MangoHuds eigene Zusammenfassung wird nicht verwendet.** Sie rundet auf
  eine Nachkommastelle und rechnet immer über den ganzen Lauf. Sie diente
  aber als Gegenprobe: 1-%-Tief 28,6 gegen 29,3, 0,1-%-Tief 10,4 gegen 10,4.

- **Der Taktregler steht im Protokoll.** MangoHud schreibt ihn in die
  Kopfzeile; SPIELRaum zeigt ihn mit an. Damit lässt sich nachprüfen, ob
  GameMode gegriffen hat, statt es zu glauben. Stehen zwei verglichene Läufe
  auf verschiedenen Reglern, gibt es einen Hinweis – sonst misst man den
  Regler statt der Änderung.

- **Unterschiede unter drei Prozent gelten als keine.** Zwei Läufe desselben
  Spiels schwanken auch ohne Zutun. Ein Programm, das jede Schwankung als
  Erfolg verkauft, ist ein schlechter Ratgeber.

- **Anleitung** in [docs/messen.md](docs/messen.md).

### Behoben

- **Der 1-%-Tiefstwert war um eine Stelle daneben.** Bei 200 Stichproben ist
  das unterste Prozent an Stelle 0 und 1; gerechnet wurde aber mit Stelle 2 –
  dem ersten Wert, der *nicht* mehr dazugehört. Ein Protokoll mit zwei
  Rucklern unter zweihundert Stichproben meldete damit die volle Bildrate als
  Tiefstwert, also genau das Gegenteil des Gesuchten. Gefunden hat es
  `test_tiefstwerte`, nicht das Auge.

## [0.2.0] – 2026-09-30

Der Befehl, um den es geht, ist da. SPIELRaum startet Spiele, richtet das
System dafür her und räumt hinterher auf – auch nach einem Absturz.

### Hinzugefügt

- **`spielraum starten`** (`spielraum/starten.py`). Gehört in die
  Steam-Startoptionen eines Spiels:

      spielraum starten %command%

  Erkannt wird das Spiel an der `SteamAppId` aus der Umgebung. Wo das Spiel
  liegt, wird bei **jedem** Start neu gesucht, nie aus dem Profil gelesen –
  ein deinstalliertes und neu geladenes Spiel liegt womöglich in einer
  anderen Bibliothek.

  Gibt es kein Profil, startet das Spiel unverändert. Alles andere wäre eine
  Falle: Wer SPIELRaum einträgt und später das Profil löscht, stünde sonst
  vor einem Spiel, das nicht mehr anspringt, und suchte den Fehler überall,
  nur nicht in den Startoptionen.

- **Stellschrauben mit Sicherung** (`spielraum/stellschrauben.py`). Vor jeder
  Änderung an einer Spieldatei wird eine Kopie abgelegt und der Verweis
  darauf ins Journal geschrieben – in dieser Reihenfolge.

  Zwei der wirksamsten Stellschrauben sind dabei gar keine: GameMode und die
  Sperre gegen Bildschirmschoner und Ruhezustand sind *Wrapper*. Ihre Wirkung
  endet mit dem Prozess. Was sich nicht verstellen lässt, kann auch nicht
  hängenbleiben. Die Befehlskette ist

      systemd-inhibit  gamemoderun  <Spiel>

- **Die Umgebung wird kopiert, nicht verstellt.** Das Spiel bekommt eine
  eigene Umgebung mit; `os.environ` des laufenden SPIELRaum bleibt unberührt.
  Auch hier gibt es damit nichts zurückzusetzen.

- **`spielraum aufraeumen` setzt jetzt wirklich zurück** statt nur
  anzuzeigen. `--zeigen` behält das alte Verhalten, für den, der erst
  nachsehen will.

- **`--trocken`** zeigt, was geschähe, ohne etwas zu ändern oder zu starten.
  Wer einem Programm erlaubt, in die Dateien seiner Spiele zu schreiben, soll
  vorher nachsehen dürfen.

- **Signale werden an das Spiel weitergereicht.** Ohne das gäbe es einen
  hässlichen Fall: Beim Abmelden schickt systemd SIGTERM, Python bräche sofort
  ab, das Spiel liefe verwaist weiter und zurückgesetzt würde zu früh.

### Geprüft

Neun Tests zu `stellschrauben`, darunter der Fall, für den das ganze Journal
existiert: Datei geändert, Prozess tot, niemand da zum Aufräumen – beim
nächsten Start muss SPIELRaum das allein hinbekommen. Danach ist die Datei
Byte für Byte wieder die alte.

## [0.1.0] – 2026-09-30

Der erste Aufschlag. Das Gerüst steht, der Kern ist geprüft, der Befehl, um
den es eigentlich geht, fehlt noch.

### Hinzugefügt

- **Systemerkennung statt fester Pfade** (`spielraum/umgebung.py`). Arch und
  Debian sind beide von Anfang an gemeint. Geprüft wird über `ID_LIKE` aus
  `/etc/os-release`, nicht über `ID` – sonst unterstützt man genau zwei
  Distributionen statt zweier Familien: Manjaro meldet sich als `manjaro`
  mit `ID_LIKE=arch`, Mint als `linuxmint` mit `ID_LIKE=ubuntu debian`.
  Fehlt ein Werkzeug, nennt die Meldung den Befehl zum Nachinstallieren –
  je nach Familie `pacman -S` oder `apt install`.

- **Profilformat** (`spielraum/profil.py`). Eine TOML-Datei pro Spiel. TOML,
  weil Python es seit 3.11 mit `tomllib` selbst liest – kein Paket
  nachzuziehen, nur um die eigene Konfiguration zu lesen, wiegt hier mehr
  als jedes Format-Argument.

  Profile enthalten **keine Befehle**, nur Werte aus einer festen Liste. Ein
  Feld, in das man eine Befehlszeile schreiben kann, wäre ein Einfallstor:
  Wer die Datei schreiben darf, führte sonst Code mit erhöhten Rechten aus.

- **Zustandsjournal mit Absturzsicherung** (`spielraum/zustand.py`). Der alte
  Wert wird gelesen und geschrieben, *bevor* geändert wird; andersherum wäre
  ein Absturz zwischen beiden Schritten nicht mehr aufzulösen. Geschrieben
  wird atomar über `os.replace` mit `fsync` davor – ohne das steht die Datei
  zwar im Verzeichnis, ihr Inhalt aber womöglich noch im Schreibpuffer, und
  genau dann nützt sie nach einem Stromausfall nichts.

- **`override.cfg` zusammenführen statt überschreiben**
  (`spielraum/godot_cfg.py`). Zeilenweise, nicht über `configparser`: Godots
  Format sieht INI ähnlich, ist aber keines, und `configparser` schreibt beim
  Zurückschreiben alles neu – Reihenfolge, Anführungszeichen und Kommentare
  gehen dabei verloren.

  Der Anlass ist konkret. Road to Vostok führt in dieser Datei seinen
  Mod-Loader an. Wer sie überschreibt, schaltet sechzehn Mods ab und merkt es
  erst, wenn das Spiel läuft und alles fehlt – es stürzt ja nicht ab. Genau
  dieser Fall steht als `test_modloader_ueberlebt` in den Tests und wurde
  zusätzlich gegen die echte Datei auf der Platte gegengeprüft.

- **Erstes Profil: Road to Vostok** (`profile/1963610-road-to-vostok.toml`).
  Nicht aus dem Lehrbuch, sondern am 30.09.2026 auf dem Rechner nachgesehen,
  auf dem das Spiel läuft.

- **Kommandozeile** mit `umgebung`, `profile`, `pruefen` und `aufraeumen`.

### Bekannte Lücken

- **`spielraum starten` gibt es noch nicht.** Das ist der Befehl, um den es
  eigentlich geht. Er wird bewusst nicht als Platzhalter angeboten: Ein
  Befehl, der so aussieht, als würde er das System herrichten, es aber nicht
  tut, ist schlimmer als keiner.

- **Der Wechsel auf Vulkan ist eine Vermutung, keine Messung.** Das
  Spielprotokoll meldet `Driver Detected: d3d12`, und Godot 4.6.2 hat Vulkan
  einkompiliert – der Umweg über vkd3d-proton ließe sich also womöglich
  sparen. Ob das mit sechzehn Mods gutgeht, weiß niemand. Die Zeile steht
  auskommentiert im Profil, bis gemessen ist.

- **Die Umgebungsvariable für den vkd3d-proton-Zwischenspeicher fehlt.** Sie
  ließ sich im Proton-Bau auf diesem Rechner nicht auffinden. Sie aus dem
  Gedächtnis hinzuschreiben wäre geraten, und geraten steht hier nichts.
