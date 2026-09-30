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
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import umgebung

JOURNAL_FASSUNG = 1


@dataclass
class Eintrag:
    """Eine einzelne Stellschraube und der Wert, auf dem sie vorher stand."""

    stellschraube: str
    ziel: str  # welche Datei, welche GPU, welche Variable
    vorher: str | None  # None heißt: gab es vorher nicht, also wieder entfernen
    nachher: str | None = None


@dataclass
class Journal:
    """Was für einen laufenden Spielstart alles verstellt wurde."""

    spiel: str
    pid: int
    fassung: int = JOURNAL_FASSUNG
    eintraege: list[Eintrag] = field(default_factory=list)

    def vermerken(self, stellschraube: str, ziel: str, vorher: str | None,
                  nachher: str | None = None) -> None:
        self.eintraege.append(Eintrag(stellschraube, ziel, vorher, nachher))


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
    """Ein Journal einlesen. Unlesbares gilt als nicht vorhanden."""
    try:
        roh = json.loads(pfad.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if roh.get("fassung") != JOURNAL_FASSUNG:
        return None
    return Journal(
        spiel=roh.get("spiel", "?"),
        pid=int(roh.get("pid", 0)),
        eintraege=[Eintrag(**e) for e in roh.get("eintraege", [])],
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
