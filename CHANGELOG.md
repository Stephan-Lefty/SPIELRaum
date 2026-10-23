[Deutsch](CHANGELOG.md) | [Übersicht](README.md) | [TODO](TODO.md)

# Änderungsprotokoll

Alle nennenswerten Änderungen an SPIELRaum stehen hier.

Das Format folgt [Keep a Changelog](https://keepachangelog.com/de/1.1.0/),
die Versionsnummern folgen [Semantic Versioning](https://semver.org/lang/de/).

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
