"""Die Messfahrt: drei Läufe, drei Varianten, eine Tabelle.

Ohne sie geht das Vergleichen von Einstellungen so: ins Spielmenü,
umstellen, spielen, beenden, Zahlen ansehen, wieder ins Menü. Sechsmal
hintereinander, und wer sich verzählt, vergleicht hinterher Äpfel mit
Birnen.

**Die eigentliche Schwierigkeit:** SPIELRaum läuft nicht durchgehend. Es
hängt als Umhüllung am Spielstart, lebt für die Dauer des Spiels und
beendet sich mit ihm. Zwischen zwei Läufen einer Messfahrt existiert kein
Prozess, der sich etwas merken könnte.

Deshalb liegt die Fahrtenakte auf der Platte. Dasselbe Muster wie beim
Zustandsjournal in ``zustand.py``, mit einem Unterschied: Das Journal gilt
für **einen** Spielstart und wird am Ende gelöscht. Die Fahrtenakte
überlebt mehrere Starts und verschwindet erst, wenn die Fahrt abgeschlossen
oder abgebrochen ist.

Daraus folgt eine Regel, die hier zentral ist: **Der Ausgangszustand steht
in der Fahrtenakte, nicht nur im Journal.** Bricht jemand nach dem zweiten
Lauf ab, muss SPIELRaum wissen, worauf zurückzustellen ist – das Journal
des zweiten Laufs kennt nur den Zustand von Lauf eins.

**Wer führt:** nicht diese Datei und nicht die Umhüllung, sondern die
Oberfläche. ``spielraum starten`` setzt, was hier steht, misst und schreibt
das Ergebnis zurück – mehr nicht. Es startet insbesondere **kein Spiel
neu**. Wer nach dem ersten Lauf keine Lust mehr hat, soll nicht gegen ein
Spiel ankämpfen, das sich von selbst wieder öffnet.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

from . import umgebung

FAHRT_FASSUNG = 2

# Welche Fassungen noch gelesen werden. Fassung 1 kannte die CPU-Last pro
# Lauf nicht; das ist ein fehlendes Feld, kein anderer Aufbau. Eine solche
# Akte wegzuwerfen hieße, eine fertig gemessene Fahrt zu verlieren, weil
# eine Spalte dazugekommen ist. Dieselbe Entscheidung wie beim
# Zustandsjournal, siehe zustand.GELESENE_FASSUNGEN.
GELESENE_FASSUNGEN = (1, 2)

# Wie lange ein Lauf mindestens dauern muss, damit er zählt. Keine
# Schikane, sondern Folge einer Messung vom 01.10.2026: Zwei Läufe
# desselben Spiels ohne Änderung dazwischen ergaben 60,6 Bilder/s über
# fünf Minuten und 46,1 über vierzig. Der kurze Lauf zeigte 31 % mehr --
# nicht weil etwas besser war, sondern weil zufällig wenig los war.
MINDESTDAUER = 600.0  # Sekunden, nach Abzug der Ladezeit


@dataclass
class Lauf:
    """Ein erledigter Abschnitt der Fahrt."""

    variante: str
    messdatei: str | None = None
    mittel: float = 0.0
    tief_1: float = 0.0
    tief_01: float = 0.0
    dauer: float = 0.0
    # Mittlere CPU-Last im Messfenster, in Prozent. Nicht zum Bewerten,
    # sondern zum Vergleichen: Weichen zwei Läufe hier stark ab, lief beim
    # einen etwas mit, und der Vergleich taugt nicht. 0.0 heißt »nicht
    # mitgeschrieben« - bei Akten aus Fassung 1 ist das der Normalfall.
    cpu_last: float = 0.0
    # Warum ein Lauf nicht zählt. Leer heißt: er zählt.
    verworfen: str = ""

    @property
    def zaehlt(self) -> bool:
        return not self.verworfen and self.messdatei is not None


@dataclass
class Fahrt:
    """Eine laufende Messfahrt über mehrere Spielstarts hinweg."""

    spiel: str
    steam_app_id: int
    varianten: list[str]
    # Die Werte, auf denen die Einstellungsdatei vor dem ersten Eingriff
    # stand. Als Pfad zu einer Sicherung, nicht als Werteliste: Eine
    # Sicherung umfasst auch, was SPIELRaum gar nicht kennt.
    ausgangszustand: str | None = None
    angelegt: float = 0.0
    # Abgeschlossen heißt: ausgewertet und entschieden. Die Akte bleibt
    # danach liegen -- als Ergebnisspeicher und als Merker, dass hier schon
    # gemessen wurde. Ohne das begänne bei eingeschalteter Automatik nach
    # jedem Verwerfen sofort die nächste Fahrt.
    abgeschlossen: bool = False
    uebernommen: str = ""
    fassung: int = FAHRT_FASSUNG
    laeufe: list[Lauf] = field(default_factory=list)

    @property
    def naechste(self) -> str | None:
        """Welche Variante beim nächsten Spielstart gesetzt wird.

        Verworfene Läufe zählen nicht: Derselbe Schritt wird wiederholt.
        """
        erledigt = [l.variante for l in self.laeufe if l.zaehlt]
        for name in self.varianten:
            if name not in erledigt:
                return name
        return None

    @property
    def fertig(self) -> bool:
        return self.naechste is None

    def abschliessen(self, uebernommen: str = "") -> None:
        """Die Fahrt beenden, ohne die Zahlen wegzuwerfen."""
        self.abgeschlossen = True
        self.uebernommen = uebernommen

    @property
    def stand(self) -> str:
        return f"{sum(1 for l in self.laeufe if l.zaehlt)} von {len(self.varianten)}"

    def vermerken(self, lauf: Lauf) -> None:
        """Einen Lauf eintragen – und einen früheren verworfenen ersetzen.

        Ohne das Ersetzen sammelt sich bei jedem Fehlversuch ein weiterer
        Eintrag an, und die Übersicht wird zur Fehlerliste.
        """
        self.laeufe = [l for l in self.laeufe
                       if not (l.variante == lauf.variante and not l.zaehlt)]
        self.laeufe.append(lauf)

    def beste(self) -> Lauf | None:
        """Die Variante mit dem höchsten 1-%-Tiefstwert.

        Nicht der Mittelwert: Der sagt, wie es im Durchschnitt aussah. Der
        1-%-Tiefstwert sagt, wie schlecht es in den schlechtesten Momenten
        wurde – und die sind es, die man als Ruckeln wahrnimmt.
        """
        zaehlende = [l for l in self.laeufe if l.zaehlt]
        return max(zaehlende, key=lambda l: l.tief_1) if zaehlende else None

    def mitlaeufer_hinweis(self) -> str | None:
        """Weichen die zählenden Läufe in der CPU-Last stark ab?

        Dann wurden nicht zwei Varianten verglichen, sondern zwei
        Rechnerzustände. Die Fahrt verwirft deswegen nichts -- sie sagt es.
        Zum Hintergrund siehe ``messen.MITLAEUFER_SPANNE``.
        """
        from . import messen

        lasten = {l.variante: l.cpu_last for l in self.laeufe
                  if l.zaehlt and l.cpu_last}
        if len(lasten) < 2:
            return None
        hoch = max(lasten, key=lambda n: lasten[n])
        tief = min(lasten, key=lambda n: lasten[n])
        abstand = lasten[hoch] - lasten[tief]
        if abstand < messen.MITLAEUFER_SPANNE:
            return None
        return (f"Die Läufe sind in der CPU-Last {abstand:.0f} Prozentpunkte "
                f"auseinander (»{tief}« {lasten[tief]:.0f} %, »{hoch}« "
                f"{lasten[hoch]:.0f} %). Bei »{hoch}« lief vermutlich etwas "
                f"mit – Bildschirmaufnahme, Fernwartung, ein zweites Spiel. "
                f"Dann vergleicht diese Fahrt nicht zwei Varianten, sondern "
                f"zwei Rechnerzustände. Den Lauf besser wiederholen.")


# --- Auf der Platte --------------------------------------------------------


def fahrten_verzeichnis() -> Path:
    """Wo die Akten liegen. Unter *data*, nicht unter *runtime*.

    Anders als das Zustandsjournal muss eine Fahrtenakte einen Neustart
    überleben: Zwischen zwei Läufen können Tage liegen.
    """
    ordner = umgebung.daten_verzeichnis() / "fahrten"
    ordner.mkdir(parents=True, exist_ok=True)
    return ordner


def akte_pfad(app_id: int) -> Path:
    return fahrten_verzeichnis() / f"{app_id}.json"


def schreiben(fahrt: Fahrt) -> Path:
    """Atomar schreiben: erst daneben, dann umbenennen.

    Eine halb geschriebene Akte wäre schlimmer als keine – sie sieht
    gültig aus und schickt den nächsten Lauf auf eine falsche Variante.
    """
    ziel = akte_pfad(fahrt.steam_app_id)
    text = json.dumps(asdict(fahrt), indent=2, ensure_ascii=False)
    with tempfile.NamedTemporaryFile("w", dir=ziel.parent, delete=False,
                                     encoding="utf-8") as datei:
        datei.write(text)
        datei.flush()
        os.fsync(datei.fileno())
        vorlaeufig = Path(datei.name)
    os.replace(vorlaeufig, ziel)
    return ziel


def lesen(app_id: int) -> Fahrt | None:
    """Die Akte zu diesem Spiel – oder None, wenn keine Fahrt läuft."""
    pfad = akte_pfad(app_id)
    try:
        roh = json.loads(pfad.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if roh.get("fassung") not in GELESENE_FASSUNGEN:
        # Eine Akte aus einer unbekannten Fassung wird nicht geraten,
        # sondern liegengelassen. Der Aufrufer meldet sie beim Aufräumen.
        return None
    # Nur bekannte Felder übernehmen. Lauf(**l) würde an einem Feld
    # scheitern, das eine neuere Fassung hinzufügt - und zwar mit einem
    # TypeError mitten im Spielstart.
    erlaubt = {f.name for f in fields(Lauf)}
    laeufe = [Lauf(**{k: v for k, v in l.items() if k in erlaubt})
              for l in roh.pop("laeufe", [])]
    bekannt = {f.name for f in fields(Fahrt)} - {"laeufe"}
    roh = {k: v for k, v in roh.items() if k in bekannt}
    # Die Akte wird in der aktuellen Fassung weitergeführt, sobald sie
    # das nächste Mal geschrieben wird.
    roh["fassung"] = FAHRT_FASSUNG
    return Fahrt(**roh, laeufe=laeufe)


def entfernen(app_id: int) -> None:
    akte_pfad(app_id).unlink(missing_ok=True)


def alle() -> list[Fahrt]:
    """Alle liegenden Akten – für das Aufräumen und die Oberfläche."""
    gefunden = []
    for pfad in sorted(fahrten_verzeichnis().glob("*.json")):
        if pfad.stem.isdigit():
            fahrt = lesen(int(pfad.stem))
            if fahrt is not None:
                gefunden.append(fahrt)
    return gefunden


# --- Bewerten --------------------------------------------------------------


def pruefen(kennzahlen, mindestdauer: float = MINDESTDAUER) -> str:
    """Zählt dieser Lauf? Gibt den Grund zurück, warum nicht – oder "".

    Die Prüfung sitzt hier und nicht in der Oberfläche, damit sie für den
    Weg über die Kommandozeile genauso gilt.
    """
    if kennzahlen is None:
        return "Keine verwertbare Messung – hat MangoHud mitgeschrieben?"
    spielzeit = kennzahlen.dauer - kennzahlen.ladezeit
    if spielzeit < mindestdauer:
        return (f"Nur {spielzeit / 60:.1f} Minuten gespielt, nötig sind "
                f"{mindestdauer / 60:.0f}. Kurze Läufe zeigen zu hohe Werte: "
                f"Am 01.10.2026 ergaben fünf Minuten 60,6 Bilder/s und "
                f"vierzig Minuten 46,1 – bei identischen Einstellungen.")
    return ""
