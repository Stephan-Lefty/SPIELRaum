"""Das Journal: was SPIELRaum verändert hat und wie es zurückgeht.

Der schwierigste Teil des ganzen Programms ist nicht das Optimieren – das sind
ein paar Schreibvorgänge. Schwierig ist die Zusage, **dass es hinterher wieder
so ist wie vorher.** Auch dann, wenn das Spiel abstürzt. Auch dann, wenn der
Rechner hart ausgeht. Auch dann, wenn SPIELRaum selbst abgeschossen wird.

Die Antwort darauf sind vier Netze, eines unter dem anderen:

1. **Vor jeder Änderung wird der alte Wert gelesen und ins Journal
   geschrieben** – erst dann wird geändert. Andersherum wäre ein Absturz
   zwischen beiden Schritten nicht mehr aufzulösen.
2. **Das Journal liegt auf der Platte, nicht im Speicher.** Ein Journal im
   Arbeitsspeicher stirbt mit dem Prozess, der es braucht.
3. **Geschrieben wird atomar** (Datei daneben, dann umbenennen). Ein halb
   geschriebenes Journal ist schlimmer als keines: Es sieht gültig aus.
4. **Beim nächsten Start wird nach verwaisten Journalen gesehen.** Liegt eines
   da, dessen Prozess nicht mehr lebt, wird zuerst aufgeräumt und dann erst
   gestartet.

Das Journal ist bewusst dumm: eine Liste von Einträgen »Stellschraube X stand
auf Y«. Es enthält keine Befehle, nur Werte. Zurückgesetzt wird in umgekehrter
Reihenfolge des Setzens.

**Netz 1 meint den Wert, nicht die Datei.** Bis zum 03.11.2026 stand bei
Dateien nur der Pfad einer Vollsicherung im Journal, und zurückgesetzt wurde,
indem diese Sicherung zurückkopiert wurde. Das setzt mehr zurück als die
eigene Änderung: Alles, was das Spiel während des Laufs selbst in dieselbe
Datei schreibt, war hinterher weg. Bei Road to Vostok traf es die
Tastenbelegung – und weil jeder Lauf denselben Stand zurückholte, konnte die
Datei fünf Wochen lang gar nicht mehr anders werden. Seit Fassung 2 steht im
Journal, was die angefassten **Schlüssel** vorher enthielten.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

from . import umgebung

JOURNAL_FASSUNG = 2

# Fassungen, die ``lesen`` noch annimmt. Ein Journal, das nicht gelesen wird,
# ist ein Journal, das nicht zurücksetzt – damit fiele das vierte Netz aus.
# Beim Sprung auf Fassung 2 am 03.11.2026 lag auf dem Rechner ein Journal der
# Fassung 1; hätte ``lesen`` es verworfen, wäre eine liegende Tastenbelegung
# bis zum Neustart stehen geblieben.
GELESENE_FASSUNGEN = (1, 2)


@dataclass
class Eintrag:
    """Eine einzelne Stellschraube und der Wert, auf dem sie vorher stand."""

    stellschraube: str
    ziel: str  # welche Datei, welche GPU, welche Variable
    vorher: str | None  # None heißt: gab es vorher nicht, also wieder entfernen
    nachher: str | None = None

    # --- Ab Journalfassung 2: die alten Werte einzeln -----------------------
    #
    # ``vorher`` ist bei Dateien der Pfad einer Vollsicherung. Sie beim
    # Zurücksetzen zurückzukopieren war der Fehler vom 03.11.2026: Damit
    # verschwand auch alles, was das Spiel selbst in dieselbe Datei
    # geschrieben hatte – bei Road to Vostok die Tastenbelegung, die
    # Lautstärken, das Blickfeld. Fünf Wochen lang konnte sich die Datei
    # dadurch überhaupt nicht mehr ändern.
    #
    # Deshalb steht hier jetzt, was die **von uns angefassten** Schlüssel
    # vorher enthielten – als Text, genau so wie sie in der Datei standen.
    # Zurückgesetzt wird, indem diese Werte in die *aktuelle* Datei
    # zurückgeschrieben werden. Die Vollsicherung bleibt als Netz darunter,
    # nicht als Weg.
    #
    # ``art`` sagt, welcher Schreiber zuständig ist; ohne die Angabe müsste
    # das Zurücksetzen das Dateiformat erraten.
    art: str | None = None
    alt_werte: dict | None = None

    # Abschnitte, die es vor unserer Änderung gar nicht gab. Beim
    # Zurücksetzen muss auch ihre Kopfzeile weichen, sonst bleibt ein
    # ``[rendering/renderer]`` stehen, das SPIELRaum selbst angelegt hat.
    fehlende_abschnitte: list | None = None


@dataclass
class Journal:
    """Was für einen laufenden Spielstart alles verstellt wurde."""

    spiel: str
    pid: int
    fassung: int = JOURNAL_FASSUNG
    eintraege: list[Eintrag] = field(default_factory=list)

    def vermerken(self, stellschraube: str, ziel: str, vorher: str | None,
                  nachher: str | None = None, art: str | None = None,
                  alt_werte: dict | None = None,
                  fehlende_abschnitte: list | None = None) -> None:
        self.eintraege.append(
            Eintrag(stellschraube, ziel, vorher, nachher, art, alt_werte,
                    fehlende_abschnitte))


def journal_pfad(spiel: str) -> Path:
    """Ein Journal je Spiel, damit zwei gleichzeitig laufende sich nicht stören."""
    sicher = "".join(z if z.isalnum() or z in "-_" else "_" for z in spiel)
    return umgebung.laufzeit_verzeichnis() / f"{sicher}.journal.json"


def schreiben(journal: Journal) -> Path:
    """Das Journal atomar ablegen.

    ``os.replace`` ist auf POSIX atomar: Entweder liegt die alte Fassung da
    oder die neue, nie eine halbe. Das ``flush``/``fsync`` davor ist kein
    Zierrat – ohne sie steht die Datei zwar im Verzeichnis, ihr Inhalt aber
    womöglich noch im Schreibpuffer, und genau dann nützt sie nach einem
    Stromausfall nichts.
    """
    pfad = journal_pfad(journal.spiel)
    pfad.parent.mkdir(parents=True, exist_ok=True)
    daten = json.dumps(asdict(journal), ensure_ascii=False, indent=2)

    griff, zwischendatei = tempfile.mkstemp(dir=pfad.parent, suffix=".tmp")
    try:
        with os.fdopen(griff, "w", encoding="utf-8") as datei:
            datei.write(daten)
            datei.flush()
            os.fsync(datei.fileno())
        os.replace(zwischendatei, pfad)
    except BaseException:
        Path(zwischendatei).unlink(missing_ok=True)
        raise
    return pfad


def lesen(pfad: Path) -> Journal | None:
    """Ein Journal einlesen. Unlesbares gilt als nicht vorhanden.

    Ältere Fassungen werden angenommen, nicht verworfen: Die neuen Felder
    haben Vorgabewerte, und ein Eintrag ohne ``alt_werte`` wird beim
    Zurücksetzen über die Vollsicherung aufgelöst – den alten Weg. Nur so
    räumt eine neue Fassung auch hinter der vorigen auf.
    """
    try:
        roh = json.loads(pfad.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if roh.get("fassung") not in GELESENE_FASSUNGEN:
        return None

    bekannt = {f.name for f in fields(Eintrag)}
    eintraege = []
    for e in roh.get("eintraege", []):
        if not isinstance(e, dict) or "stellschraube" not in e:
            continue
        # Unbekannte Felder wegwerfen statt am Aufruf zu scheitern: Ein
        # Journal einer *neueren* Fassung soll nicht dazu führen, dass gar
        # nichts zurückgesetzt wird.
        eintraege.append(Eintrag(**{k: v for k, v in e.items() if k in bekannt}))

    return Journal(
        spiel=roh.get("spiel", "?"),
        pid=int(roh.get("pid", 0)),
        fassung=int(roh.get("fassung", JOURNAL_FASSUNG)),
        eintraege=eintraege,
    )


def entfernen(spiel: str) -> None:
    journal_pfad(spiel).unlink(missing_ok=True)


def laeuft_noch(pid: int) -> bool:
    """Lebt der Prozess, der dieses Journal angelegt hat?

    ``os.kill(pid, 0)`` sendet kein Signal, sondern prüft nur. Die Nummer kann
    inzwischen einem fremden Prozess gehören – für unseren Zweck reicht das
    trotzdem: Wir wollen wissen, ob wir gefahrlos aufräumen dürfen, und im
    Zweifel räumen wir lieber nicht auf.
    """
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # Es gibt ihn, er gehört nur jemand anderem.
        return True
    return True


def verwaiste_journale() -> list[Journal]:
    """Journale, deren Prozess nicht mehr lebt – Spuren eines Absturzes."""
    verzeichnis = umgebung.laufzeit_verzeichnis()
    if not verzeichnis.is_dir():
        return []
    gefunden = []
    for pfad in sorted(verzeichnis.glob("*.journal.json")):
        journal = lesen(pfad)
        if journal is not None and not laeuft_noch(journal.pid):
            gefunden.append(journal)
    return gefunden
