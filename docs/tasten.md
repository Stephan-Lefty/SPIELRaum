# Tastenbelegung pro Spiel

## Das Problem

Wer die Maus links führt, bedient die Tastatur rechts. Erreichbar ist dann
ohne Umgreifen nur der Bereich ab I/K/M nach rechts: Pfeiltasten, der
Sechserblock darüber, Enter, die rechten Modifikatoren.

Spiele legen ihre Befehle aber auf WASD, Leertaste und die linke
Umschalttaste – alles unter der *linken* Hand. Die ist hier an der Maus.

Jedes Spiel einzeln umzustellen hilft nur begrenzt. Manche bieten es nicht
an, bei jedem neuen Spiel fängt die Arbeit von vorn an, und die Begriffe
unterscheiden sich: Was in einem Spiel `Sneak` heißt, heißt im nächsten
`Crouch` und im dritten gar nicht.

## Der Weg: keyd, aber auf Zeit

[keyd](https://github.com/rvaiya/keyd) setzt Tasten auf Systemebene um, und
zwar **pro Gerät**. Damit lässt sich eine Spieltastatur umbelegen, ohne die
Arbeitstastatur anzurühren.

SPIELRaum setzt die Belegung **beim Spielstart** und nimmt sie beim Beenden
zurück – dieselbe Zusage wie bei allem anderen hier.

### Warum nicht dauerhaft in `/etc/keyd`?

Weil es am 23.10.2026 genau so anfing und sofort störte: Die Pfeiltaste
schrieb auch im Browser ein `w`. Eine Übersetzung, die immer gilt, ist keine
Spieleinstellung, sondern ein neues Tastaturlayout.

Die Datei unter `/etc/keyd/` legt deshalb **keine einzige Taste** um. Sie
sagt keyd nur, welches Gerät es beobachten soll:

```
[ids]

6332:3663

[main]

# Leer. Hier steht mit Absicht nichts.
```

### Warum ohne root?

keyd legt einen Socket unter `/run/keyd.socket` an, der der Gruppe `keyd`
gehört:

```
srw-rw---- 1 root keyd 0 /run/keyd.socket
```

Wer in dieser Gruppe ist, darf dem laufenden Dienst Belegungen schicken.
Kein Polkit, kein Passwortdialog, kein `sudo` – und vor allem: SPIELRaum
braucht selbst keine erhöhten Rechte.

Das unterscheidet diesen Fall von GameMode, wo die Polkit-Regel des
Manjaro-Pakets auf `allow_active=no` steht und deshalb nichts ausrichtet
(siehe `docs/gamemode.md`).

## Einrichten

Drei Schritte, einmalig:

```
sudo pacman -S keyd                      # auf Debian: sudo apt install keyd
sudo usermod -aG keyd $USER
sudo systemctl enable --now keyd
```

Danach **ab- und wieder anmelden**. Gruppenmitgliedschaften gelten erst für
eine neue Sitzung; `id` zeigt die Gruppen der Anmeldung, nicht die der
Systemdatenbank.

Dann eine Datei unter `/etc/keyd/` anlegen, die das eigene Gerät benennt.
Die Kennung findet man so:

```
lsusb
```

Zum Prüfen:

```
keyd check /etc/keyd/meine-tastatur.conf
```

> **Falle:** keyd versteht keine Kommentare am Zeilenende. Es verwirft
> solche Zeilen mit einer bloßen Warnung statt mit einem Abbruch – sechs
> Belegungen waren am 23.10.2026 still verschwunden, bis `keyd check` es
> meldete. Hinweise gehören in eigene Zeilen.

## Im Profil

```toml
[tasten]

up    = "w"
down  = "s"
left  = "a"
right = "d"

pageup   = "space"
pagedown = "layer(shift)"
end      = "layer(control)"
```

Links steht, was gedrückt wird. Rechts, was das Spiel sehen soll.

`layer(shift)` statt `leftshift`: Sonst schickt keyd nur den Tastencode,
ohne ihn als Modifikator zu führen. Beim Sprinten hält man die Taste und
bewegt sich gleichzeitig – das muss zusammengehen.

### Die Spielbelegung muss auf Vorgabe stehen

Das Übersetzen macht die Tastatur, nicht das Spiel. Stellt man beides um,
heben sie sich auf: Man drückt Bild hoch, keyd schickt die Leertaste, und
das Spiel wartet auf Bild hoch.

Am 23.10.2026 führte das zu zwei falschen Zuordnungen, die erst eine
Gegenprobe zutage förderte – *Ende* löste Ausweichen statt Schleichen aus,
*Entf* das Baumenü statt des Rucksacks.

### Was geprüft wird

Alle Namen laufen gegen die Liste, die `keyd list-keys` ausgibt. Ein Profil
ist eine Datei, die jeder bearbeiten kann; was daraus in einen Aufruf
wandert, muss gegen eine feste Liste geprüft werden. Siehe die
Sicherheitsregel in `CLAUDE.md`.

Eine zweite Liste im Profilcode gibt es bewusst nicht – sie würde mit jeder
keyd-Fassung veralten.

## Ein Blatt zum Danebenlegen

```
python3 werkzeuge/tastenblatt.py 1963610 tastenblaetter/Road-to-Vostok.md
```

Das Werkzeug liest Profil und Spieldatei und schreibt eine Übersicht in
Markdown. Entscheidend daran: Es zeigt die Taste, die **gedrückt** wird --
nicht die, die im Spielmenü steht. Seit keyd dazwischensitzt, sind das zwei
verschiedene Dinge.

Der Ordner `tastenblaetter/` wird von Git ignoriert. Die Belegung hängt an
der Hand, die die Maus führt, und an den Tastaturen auf dem Tisch -- sie
gehört niemandem sonst.

Liegt dort eine Datei, deren Name mit dem Spielnamen beginnt, verweist die
Oberfläche von selbst darauf.

> Am 23.10.2026 entstanden zwei solche Übersichten aus Wegwerfskripten in
> `/tmp`. Fünf Minuten später waren sie falsch, weil die Belegung sich
> geändert hatte, und am Abend waren die Skripte weg. Was aus den echten
> Quellen erzeugt wird, kann nicht veralten.

## Zurücksetzen

`keyd bind reset` verwirft alles, was zur Laufzeit gesetzt wurde. Weil die
Datei unter `/etc/keyd` keine Taste umlegt, ist die Tastatur danach wieder
das, was auf ihren Tasten steht.

Das steht als Journaleintrag unter der Stellschraube `tasten` und wird von
`spielraum/stellschrauben.py` mit abgearbeitet – auch dann, wenn SPIELRaum
abstürzt, während die Belegung liegt.

## Notbremse

Wenn die Tastatur sich merkwürdig verhält:

```
sudo systemctl stop keyd
```

Eine zweite Tastatur ist die beste Rückversicherung: keyd bindet die Regel
an die USB-Kennung, nicht an „alle Tastaturen".

> Der Dienst meldet nach `stop` den Zustand `failed`. Das ist Kosmetik:
> keyd gibt den Signalwert 15 (SIGTERM) als Rückgabewert zurück, und
> systemd deutet jeden Wert außer null als Fehler.

## Was das nicht löst

**Nicht jede Aktion lässt sich vereinheitlichen.** WASD, Leertaste, Umschalt
und Strg sind in fast jedem Spiel gleich belegt. Bei Inventar, Karte und
Menüs kocht jedes Spiel sein eigenes Süppchen. Dafür legt man besser eine
feste physische Taste fest und stellt das jeweilige Spiel einmalig darauf
ein – im Profil, nicht in `/etc/keyd`.

**Die Maus bleibt außen vor.** keyd ist für Tastaturen. Maustasten belegt
man weiterhin im Spiel.
