"""MangoHud-Protokolle auswerten und Läufe vergleichen.

Ohne diesen Teil ist SPIELRaum ein Programm, das Einstellungen verstellt und
behauptet, es sei besser geworden. Erst hier wird aus »fühlt sich flüssiger
an« ein Vorher-Nachher, das man nachrechnen kann.

## Was MangoHud schreibt

Zwei Dateien je Lauf, nachgesehen am 30.09.2026 an MangoHud 0.8.4::

    <name>_<datum>.csv           das Protokoll
    <name>_<datum>_summary.csv   MangoHuds eigene Zusammenfassung

Das Protokoll hat einen ungewöhnlichen Aufbau: **zwei Kopfzeilen**, nicht
eine. Die ersten beiden Zeilen beschreiben den Rechner, erst die dritte
nennt die Spalten::

    os,cpu,gpu,ram,kernel,driver,cpuscheduler
    Manjaro Linux,Intel Core i5-8400 …,NVIDIA GeForce GTX 1070,…,powersave
    fps,frametime,cpu_load,…,elapsed
    60.3846,16.5605,13.7124,…,100426824

Die Metadatenzeile ist mehr als Beiwerk: ``cpuscheduler`` nennt den
Taktregler, der während des Laufs galt. Damit lässt sich nachprüfen, ob
GameMode überhaupt gegriffen hat – statt es zu glauben.

``elapsed`` steht in **Nanosekunden**.

## Warum hier trotzdem selbst gerechnet wird

MangoHuds Zusammenfassung enthält bereits Mittelwert und 1-%-Tiefstwert.
Sie wird hier dennoch nicht verwendet, aus zwei Gründen:

1. Sie rundet auf eine Nachkommastelle. Bei einem Vergleich zweier Läufe,
   die nahe beieinanderliegen, ist das zu grob.
2. **Sie rechnet über den ganzen Lauf** – einschließlich der ersten
   Sekunden. Genau dort kompiliert das Spiel Shader und lädt Daten nach,
   und genau dort steht die Bildrate am schlechtesten. Wer das mitrechnet,
   misst die Ladezeit, nicht das Spiel.

Deshalb schneidet ``auswerten`` eine Aufwärmzeit ab.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

# Wie viele Sekunden am Anfang verworfen werden. Der Wert ist eine
# Abwägung: zu kurz, und die Shader-Kompilierung fließt mit ein; zu lang,
# und von einer kurzen Sitzung bleibt nichts übrig.
AUFWAERMEN = 10.0


@dataclass
class Messung:
    """Ein Lauf."""

    quelle: Path
    bilder: list[float] = field(default_factory=list)  # FPS je Stichprobe
    sekunden: list[float] = field(default_factory=list)  # elapsed, in Sekunden
    metadaten: dict[str, str] = field(default_factory=dict)

    @property
    def name(self) -> str:
        return self.quelle.stem

    @property
    def taktregler(self) -> str | None:
        """Welcher Taktregler galt? Verrät, ob GameMode gegriffen hat."""
        return self.metadaten.get("cpuscheduler") or None

    @property
    def dauer(self) -> float:
        return self.sekunden[-1] if self.sekunden else 0.0


@dataclass
class Kennzahlen:
    """Was aus einem Lauf herausgelesen wurde."""

    mittel: float
    tief_1: float  # 1-%-Tiefstwert
    tief_01: float  # 0,1-%-Tiefstwert
    stichproben: int
    dauer: float
    verworfen: int

    def __str__(self) -> str:
        return (
            f"{self.mittel:.1f} Bilder/s im Mittel, "
            f"1-%-Tief {self.tief_1:.1f}, 0,1-%-Tief {self.tief_01:.1f} "
            f"({self.stichproben} Stichproben über {self.dauer:.0f} s)"
        )


def lesen(pfad: Path) -> Messung:
    """Ein MangoHud-Protokoll einlesen.

    Robust gegen abgeschnittene Dateien: Wird ein Spiel hart beendet, bricht
    die letzte Zeile womöglich mitten im Wert ab. Solche Zeilen werden
    übersprungen, nicht als Fehler behandelt – ein abgestürztes Spiel ist
    genau der Fall, für den man die Messung haben will.
    """
    messung = Messung(quelle=pfad)

    with pfad.open(encoding="utf-8", errors="replace", newline="") as datei:
        leser = csv.reader(datei)
        try:
            meta_namen = next(leser)
            meta_werte = next(leser)
            spalten = next(leser)
        except StopIteration:
            return messung

        messung.metadaten = dict(zip(meta_namen, meta_werte))

        try:
            fps_spalte = spalten.index("fps")
            zeit_spalte = spalten.index("elapsed")
        except ValueError:
            return messung

        for zeile in leser:
            if len(zeile) <= max(fps_spalte, zeit_spalte):
                continue
            try:
                fps = float(zeile[fps_spalte])
                elapsed = float(zeile[zeit_spalte])
            except ValueError:
                continue
            if fps <= 0:
                continue
            messung.bilder.append(fps)
            messung.sekunden.append(elapsed / 1_000_000_000)  # ns -> s

    return messung


def _perzentil(sortiert: list[float], anteil: float) -> float:
    """Den Wert an einer Stelle der sortierten Liste.

    Bewusst ohne Zwischenrechnung zwischen zwei Nachbarn: Bei Bildraten ist
    ein tatsächlich gemessener Wert aussagekräftiger als ein rechnerischer,
    den so nie jemand gesehen hat.
    """
    if not sortiert:
        return 0.0
    # Das »minus eins« ist kein Schönheitsfehler, sondern der Unterschied
    # zwischen richtig und falsch: Bei 200 Stichproben sind das unterste
    # Prozent die Werte an Stelle 0 und 1. Ohne die Korrektur läge der
    # Zeigefinger auf Stelle 2 - also schon auf dem ersten Wert, der *nicht*
    # mehr dazugehört. Bei einem Protokoll mit zwei Rucklern unter zweihundert
    # Stichproben meldete SPIELRaum dann die volle Bildrate als Tiefstwert.
    stelle = max(0, int(len(sortiert) * anteil) - 1)
    return sortiert[min(stelle, len(sortiert) - 1)]


def auswerten(messung: Messung, aufwaermen: float = AUFWAERMEN) -> Kennzahlen | None:
    """Kennzahlen aus einem Lauf ziehen.

    Der 1-%-Tiefstwert ist hier das erste Perzentil der Bildraten – also
    der Wert, den ein Hundertstel der Stichproben unterschreitet. Er zählt
    mehr als der Mittelwert: Ruckler spürt man, einen guten Durchschnitt
    nicht.

    ``None``, wenn nach der Aufwärmzeit zu wenig übrig bleibt. Lieber keine
    Zahl als eine, die auf zwanzig Stichproben beruht.
    """
    # »>« und nicht »>=«: Die Stichprobe genau auf der Zehn-Sekunden-Marke
    # gehört noch zur Aufwärmphase. Ein Wert macht den Kohl nicht fett, aber
    # »die ersten zehn Sekunden« soll heißen, was es sagt.
    behalten = [
        fps for fps, sekunde in zip(messung.bilder, messung.sekunden)
        if sekunde > aufwaermen
    ]
    verworfen = len(messung.bilder) - len(behalten)

    if len(behalten) < 50:
        # Bei 100 ms Abstand sind das fünf Sekunden. Darunter ist jede
        # Aussage über Tiefstwerte Zufall.
        return None

    sortiert = sorted(behalten)
    return Kennzahlen(
        mittel=sum(behalten) / len(behalten),
        tief_1=_perzentil(sortiert, 0.01),
        tief_01=_perzentil(sortiert, 0.001),
        stichproben=len(behalten),
        dauer=messung.dauer,
        verworfen=verworfen,
    )


def laeufe(ordner: Path) -> list[Messung]:
    """Alle Läufe in einem Ordner, der jüngste zuletzt.

    Die Zusammenfassungen werden übersprungen – ihr Name endet auf
    ``_summary.csv``, und sie enthalten keine Einzelwerte.
    """
    if not ordner.is_dir():
        return []
    gefunden = []
    for pfad in sorted(ordner.glob("*.csv")):
        if pfad.name.endswith("_summary.csv"):
            continue
        messung = lesen(pfad)
        if messung.bilder:
            gefunden.append(messung)
    return gefunden


def vergleichen(vorher: Kennzahlen, nachher: Kennzahlen) -> list[str]:
    """Zwei Läufe gegenüberstellen.

    Unterschiede unter drei Prozent werden ausdrücklich als »kein
    Unterschied« ausgewiesen. Zwei Läufe desselben Spiels schwanken auch
    ohne Zutun, und ein Programm, das jede Schwankung als Erfolg verkauft,
    ist ein schlechter Ratgeber.
    """
    zeilen = []
    for was, alt, neu in (
        ("Mittel", vorher.mittel, nachher.mittel),
        ("1-%-Tief", vorher.tief_1, nachher.tief_1),
        ("0,1-%-Tief", vorher.tief_01, nachher.tief_01),
    ):
        if alt <= 0:
            continue
        anteil = (neu - alt) / alt * 100
        if abs(anteil) < 3:
            urteil = "kein nennenswerter Unterschied"
        elif anteil > 0:
            urteil = f"+{anteil:.1f} %"
        else:
            urteil = f"{anteil:.1f} %"
        zeilen.append(f"  {was:12} {alt:6.1f}  ->  {neu:6.1f}   {urteil}")
    return zeilen
