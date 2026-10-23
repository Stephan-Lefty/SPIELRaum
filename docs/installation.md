# SPIELRaum einrichten

Für Arch/Manjaro, Debian 13 und Ubuntu. Nichts davon braucht Systemrechte
für SPIELRaum selbst — nur die Pakete drumherum kommen aus der
Paketverwaltung.

> **Stand der Erprobung:** Entwickelt und täglich benutzt wird SPIELRaum auf
> Manjaro. Die CI prüft zusätzlich auf Ubuntu. **Auf einem echten Debian-13-
> Rechner ist es nie gelaufen** — die Debian-Schritte unten sind sorgfältig
> gebaut, aber nicht erprobt. Wenn etwas klemmt, ist das ein Fehler im
> Programm, nicht bei dir: Bitte melden.

## 1. Was vorher da sein muss

SPIELRaum selbst braucht nur Python 3.11 oder neuer — `tomllib` kam damit in
die Standardbibliothek. Alles andere ist freiwillig: Fehlt ein Werkzeug,
fällt genau die eine Stellschraube aus, und SPIELRaum sagt welche und wie
man sie nachrüstet.

### Arch / Manjaro

```
sudo pacman -S git python pyside6
```

Für die Stellschrauben:

```
sudo pacman -S gamemode mangohud keyd
```

### Debian 13 / Ubuntu

```
sudo apt install git python3 python3-venv python3-pyside6.qtwidgets
```

Für die Stellschrauben:

```
sudo apt install gamemode mangohud keyd
```

> **Prüfen, bevor es schiefgeht:** `keyd` liegt nicht in jeder Fassung der
> Quellen. Ob es da ist, sagt `apt-cache policy keyd`. Fehlt es, läuft alles
> andere trotzdem — nur die Tastenbelegung pro Spiel fällt aus.

> **Zum Paketnamen von PySide6:** Auf Debian 13 heißt das Paket
> `python3-pyside6.qtwidgets`. Sollte `apt` es nicht finden, hilft
> `apt-cache search pyside6` weiter. Diese Stelle ist die wahrscheinlichste
> Stolperfalle, weil sie nie an einem echten Debian geprüft wurde.

**Warum PySide6 aus der Distribution und nicht über pip?** Das Paket der
Distribution ist gegen das Qt gebaut, das auf dem Rechner liegt. Ein über
pip nachgezogenes PySide6 bringt sein eigenes Qt mit — 150 MB, die sich mit
dem System beißen können. `install.sh` legt die Python-Umgebung deshalb mit
`--system-site-packages` an, damit das Paket der Distribution sichtbar ist.

## 2. Einrichten

```
git clone https://github.com/Stephan-Lefty/SPIELRaum.git
cd SPIELRaum
./install.sh
```

Das Skript legt an:

| wohin | was |
|---|---|
| `SPIELRaum/.venv` | eine eigene Python-Umgebung |
| `~/.local/bin/spielraum` | der Starter für die Kommandozeile |
| `~/.local/bin/spielraum-ui` | der Starter für die Oberfläche |
| `~/.local/share/applications` | der Eintrag im Anwendungsmenü |
| `~/.config/spielraum/spiele` | die mitgelieferten Profile |

Vorhandene Profile bleiben unangetastet. Wer eines angepasst hat, will es
bei der nächsten Einrichtung nicht überschrieben bekommen.

Meldet das Skript am Ende, dass `~/.local/bin` nicht im Suchpfad liegt,
gehört diese Zeile in `~/.bashrc` oder `~/.zshrc`:

```
export PATH="$HOME/.local/bin:$PATH"
```

## 3. Nachsehen, ob es läuft

```
spielraum umgebung
```

Das zeigt, was SPIELRaum auf diesem Rechner gefunden hat und was fehlt —
mit dem Installationsbefehl der jeweiligen Familie daneben.

```
spielraum spiele
```

Listet die installierten Steam-Spiele und sagt, für welche es ein Profil
gibt.

## 4. In Steam eintragen

Für jedes Spiel, das SPIELRaum begleiten soll, in den **Startoptionen**:

```
spielraum starten %command%
```

Ohne diesen Eintrag startet Steam das Spiel direkt, und SPIELRaum bekommt
nichts mit: keine Messung, keine Tastenbelegung, kein Zurücksetzen.

## 5. Tastenbelegung pro Spiel (freiwillig)

Nur nötig, wenn `[tasten]` im Profil steht. Einmalig:

```
sudo usermod -aG keyd $USER
sudo systemctl enable --now keyd
```

Danach **richtig ab- und wieder anmelden** — nicht nur den Bildschirm
sperren. Gruppenmitgliedschaften werden beim Anmelden festgelegt, und jeder
Prozess erbt sie von dort. Prüfen:

```
id | grep keyd
```

Steht da `946(keyd)` oder eine andere Zahl mit `(keyd)`, ist es soweit.

Die Einzelheiten stehen in [tasten.md](tasten.md).

## Wenn etwas klemmt

**`python3 -m venv` schlägt fehl.** Auf Debian und Ubuntu steckt venv in
einem eigenen Paket: `sudo apt install python3-venv`.

**Die Oberfläche startet nicht.** Dann fehlt PySide6 oder es ist für die
Python-Umgebung nicht sichtbar. Prüfen:

```
.venv/bin/python3 -c "import PySide6; print(PySide6.__file__)"
```

Kommt ein `ImportError`, obwohl das Paket installiert ist, wurde die
Umgebung ohne `--system-site-packages` angelegt. `./install.sh` noch einmal
laufen lassen — es legt den Schalter in `.venv/pyvenv.cfg` um, statt die
Umgebung wegzuwerfen.

**`spielraum` wird nicht gefunden.** `~/.local/bin` liegt nicht im Suchpfad,
siehe oben.

**Das Spiel startet, aber nichts passiert.** Dann hat SPIELRaum kein Profil
gefunden. `spielraum spiele` zeigt, welche Spiele eines haben. Ein Profil
muss in `~/.config/spielraum/spiele` liegen, nicht im `profile/`-Ordner des
Repositorys — dort ist nur die Vorlage.

## Deinstallieren

```
rm -rf ~/.local/bin/spielraum ~/.local/bin/spielraum-ui
rm -f  ~/.local/share/applications/spielraum.desktop
rm -rf ~/.config/spielraum ~/.local/share/spielraum
```

Dazu das geklonte Verzeichnis löschen. Die Einträge in den
Steam-Startoptionen muss man von Hand entfernen — sonst startet das Spiel
nicht mehr, weil der Befehl fehlt.
