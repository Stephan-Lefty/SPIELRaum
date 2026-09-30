[Deutsch](README.md) | [English](README.en.md) | [Änderungsprotokoll](CHANGELOG.md) | [TODO](TODO.md) | [Anleitungen](docs/README.md)

# SPIELRaum

Spiele starten, das System dafür herrichten, hinterher aufräumen.

SPIELRaum merkt sich für jedes Spiel, wie der Rechner dafür stehen soll –
Taktregler, Umgebungsvariablen, Startargumente, notfalls auch eine
Einstellungsdatei des Spiels selbst. Beim Start wird das angewendet, beim
Beenden zurückgenommen. Was vorher war, war hinterher wieder.

**Für Arch/Manjaro und Debian 13.** Beide Systeme sind von Anfang an gemeint,
nicht als Nachgedanke. Kein Pfad und kein Werkzeug ist fest verdrahtet;
SPIELRaum sieht beim Start nach, was da ist, und sagt, was fehlt und wie man
es bekommt.

## Was es *nicht* nachbaut

Für den Teil mit Systemrechten – Taktregler hochsetzen, GPU auf Leistung,
Prozesspriorität – gibt es [GameMode](https://github.com/FeralInteractive/gamemode)
von Feral Interactive. Das ist erprobter Code mit einem geprüften Dienst
dahinter, und er liegt sowohl in den Arch- als auch in den Debian-Quellen.
Ihn nachzubauen hieße, eine schlechtere Fassung desselben Programms zu
schreiben.

SPIELRaum setzt darauf auf und macht das, was GameMode nicht tut:

| GameMode | SPIELRaum |
|---|---|
| ein Profil für alles | ein Profil **pro Spiel** |
| Systemstellschrauben | dazu Umgebung, Startargumente, Spieldateien |
| setzt zurück | setzt zurück, **auch nach einem Absturz** |
| — | misst nach, ob es etwas gebracht hat |

## Benutzen

In den Steam-Startoptionen des Spiels:

```
spielraum starten %command%
```

Das ist alles. SPIELRaum erkennt am `SteamAppId`, welches Spiel gemeint ist,
wendet dessen Profil an, startet, wartet und räumt hinterher auf. Gibt es kein
Profil, startet das Spiel unverändert – wer SPIELRaum einträgt und später das
Profil löscht, soll nicht vor einem Spiel stehen, das nicht mehr anspringt.

Vorher nachsehen, was passieren würde:

```
spielraum starten --profil road-to-vostok.toml --trocken -- /pfad/zum/spiel
```

Die übrigen Befehle sind zum Nachsehen:

```
spielraum spiele       # was ist installiert, und liegt es auf einer SSD?
spielraum umgebung     # was findet SPIELRaum auf diesem Rechner vor?
spielraum profile      # welche Spielprofile sind eingerichtet?
spielraum pruefen DATEI # eine Profildatei auf Fehler prüfen
spielraum aufraeumen   # nach einem Absturz Liegengebliebenes zurücksetzen
```

## Ein Profil

Ein Profil ist eine TOML-Datei pro Spiel. Sie sagt, *was* sein soll – aus
einer festen Liste bekannter Stellschrauben.

```toml
[spiel]
name         = "Road to Vostok"
steam_app_id = 1963610
engine       = "godot"

[system]
gamemode      = true
nicht_stoeren = true

[umgebung]
__GL_SHADER_DISK_CACHE_SIZE = "4294967296"

[start]
argumente = ["--rendering-driver", "vulkan"]
```

**Profile enthalten keine Befehle.** Ein Feld, in das man eine Befehlszeile
schreibt, wäre ein Einfallstor: Wer die Datei schreiben darf, führte sonst
später Code mit erhöhten Rechten aus. Das *wie* steht im Programm, nicht in
der Konfiguration.

Das mitgelieferte Profil in [`profile/`](profile/) ist keine Vorlage aus dem
Lehrbuch, sondern auf einem Rechner nachgemessen: Godot 4.6.2 unter
GE-Proton11-1, sechzehn Mods, GTX 1070 auf Wayland.

## Messen statt glauben

Ohne Messwerte ist jede Optimierung geraten. SPIELRaum schreibt deshalb über
MangoHud ein Protokoll pro Lauf und zieht daraus Mittelwert und die
1-%-Tiefstwerte – die spürt man als Ruckler, und sie sind der Grund, warum ein
guter Durchschnitt trotzdem unrund wirken kann.

Ein Selbstoptimierer wird es damit nicht. Dafür bräuchte es eine
reproduzierbare Szene, die die wenigsten Spiele hergeben. Was geht, ist ein
Messbuch über die normalen Spielsitzungen – und damit ein echtes
Vorher-Nachher statt »fühlt sich besser an«.

## Was es hinterher wieder geraderückt

Der schwierigste Teil ist nicht das Optimieren, sondern die Zusage, dass es
hinterher wieder so ist wie vorher. Auch wenn das Spiel abstürzt. Auch wenn
der Rechner hart ausgeht. Dafür gibt es vier Netze:

1. Vor jeder Änderung wird der alte Wert gelesen und ins Journal geschrieben –
   erst dann wird geändert.
2. Das Journal liegt auf der Platte, nicht im Speicher.
3. Geschrieben wird atomar. Ein halb geschriebenes Journal ist schlimmer als
   keines: Es sieht gültig aus.
4. Beim nächsten Start wird nach verwaisten Journalen gesehen.

## Einrichten

```
git clone …
cd SPIELRaum
python3 -m venv .venv
.venv/bin/pip install -e ".[entwicklung]"
.venv/bin/python -m pytest
```

Gebraucht werden Python ab 3.11 (Debian 13 bringt 3.13 mit), dazu `gamemode`
und `mangohud` aus den Paketquellen. SPIELRaum selbst hat keine einzige
Python-Abhängigkeit.

## Lizenz

[MIT](LICENSE)
