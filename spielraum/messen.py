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
import textwrap
from dataclasses import dataclass, field
from pathlib import Path

# Wie viele Sekunden nach dem ersten richtigen Bild noch verworfen werden.
#
# Achtung, hier steckte ein Fehler: Bis 0.3.0 waren das zehn Sekunden **ab
# Programmstart**. Beim ersten Lauf mit einem echten Spiel stellte sich
# heraus, dass Road to Vostok von einer drehenden Platte **23,8 Sekunden**
# lädt. Die Ladephase lag damit vollständig im Messfenster, und weil dort
# Werte wie 0,00003 Bilder/s stehen, fiel der 1-%-Tiefstwert auf null.
# SPIELRaum meldete also »1-%-Tief 0,0« für ein Spiel, das durchgehend um
# die fünfzig Bilder lieferte.
#
# Eine feste Zeit kann das nicht lösen - Ladezeiten hängen an Spiel,
# Datenträger und Mods. Deshalb wird jetzt gesucht, wann das Spiel
# tatsächlich anfängt zu rendern, und von dort aus gezählt.
AUFWAERMEN = 5.0

# Ab wann gilt ein Bild als gerendert? Während des Ladens schreibt MangoHud
# Werte in der Größenordnung 0,00003 - das ist kein langsames Spiel, das ist
# gar keines. Fünf Bilder in der Sekunde ist niedrig genug, um echte
# Ruckler nicht zu verschlucken, und hoch genug, um Ladebilder zu erkennen.
LAEUFT_AB = 5.0

# Ab welchem Unterschied in der CPU-Last zwei Läufe nicht mehr vergleichbar
# sind, in Prozentpunkten.
#
# Der Anlass, 12.11.2026: Während eines Messlaufs von Road to Vostok nahm
# OBS auf und kodierte dabei auf dem Prozessor. Aufgefallen ist es nur, weil
# die Aufnahme mitten im Lauf endete - danach sprang die Bildrate von 48,8
# auf 57,7. Derselbe Streckenabschnitt gegen den Lauf zwei Tage davor
# gerechnet: 17 Prozent. Mehr, als in diesem Projekt je eine Einstellung
# gebracht hat. Die Messung war wertlos, und zwei daraus gezogene Schlüsse
# standen schon im Repo, bevor es auffiel.
#
# Die Zahl kommt aus den vier Läufen, die es dazu gibt. Mittlere CPU-Last
# über die ersten zwölf Minuten:
#
#   Optik    05.11. .... 26,1 %
#   Leistung 09.11. .... 25,7 %
#   Leistung 10.11. .... 28,6 %
#   Leistung 12.11. .... 68,9 %   <- OBS
#
# Zwischen den drei sauberen Läufen liegen 2,9 Punkte, zum vierten 40. Zehn
# Punkte liegen deutlich über dem einen und weit unter dem anderen. Das ist
# keine hergeleitete Schwelle, sondern eine Hausnummer aus vier Läufen --
# und sie steht hier, damit sie nachgerechnet werden kann.
#
# Wichtig: Verglichen wird nur die Differenz zwischen zwei Läufen DESSELBEN
# Spiels. Ein absoluter Grenzwert wäre falsch - 70 % CPU-Last können bei
# einem Spiel der Mitläufer und beim nächsten der Normalfall sein.
#
# Und noch eine Grenze, am selben Tag beim Durchtesten gefunden: Nicht nur
# die Höhe, auch die SPANNE ist je Spiel verschieden. Bei Road to Vostok
# liegen die sauberen Läufe innerhalb von 2,9 Punkten, bei Enshrouded von
# 38,9 bis 53,0 - vierzehn Punkte, ganz ohne Mitläufer. Diese zehn Punkte
# sind also an einem Spiel kalibriert und für ein prozessorhungriges Spiel
# womöglich zu eng. Deshalb wird nur ein PAAR verglichen und nicht Höchst
# gegen Tiefst über viele Läufe; sonst schlägt es bei Enshrouded immer an.
# Der offene Punkt dazu steht in TODO.md.
MITLAEUFER_SPANNE = 10.0

# Wie lange ein Lauf gemessen sein muss, damit seine CPU-Last etwas über die
# Sitzung sagt -- in Sekunden Spielzeit, nach Abzug der Ladezeit.
#
# Ohne diese Grenze stützte sich die Warnung am 12.11.2026 auf einen Lauf von
# **13 Sekunden** und meldete 42 Prozentpunkte Unterschied, wo in den
# brauchbaren Läufen 32 lagen. Also derselbe Fehler, den die Warnung
# verhindern soll: eine Zahl aus zu wenig Material.
#
# Eine Minute ist ein Fußboden, keine hergeleitete Grenze. Begründung: Im
# Lauf vom 12.11. schwankten die Minutenmittel der CPU-Last zwischen 36 und
# 82 Prozent. Unterhalb einer Minute misst man eine Ladespitze oder einen
# Dienst, der gerade fertig wird -- nicht, was während des Spielens lief.
#
# Nicht zu verwechseln mit ``fahrt.MINDESTDAUER`` (zehn Minuten). Das ist
# die Grenze, ab der eine BILDRATE etwas aussagt, und sie ist höher.
MITLAEUFER_MINDESTZEIT = 60.0


@dataclass
class Messung:
    """Ein Lauf."""

    quelle: Path
    bilder: list[float] = field(default_factory=list)  # FPS je Stichprobe
    sekunden: list[float] = field(default_factory=list)  # elapsed, in Sekunden
    # CPU-Last je Stichprobe, in Prozent. Leer, wenn das Protokoll die
    # Spalte nicht hat - MangoHud lässt sich so einstellen. Fehlt sie, gibt
    # es eben keine Mitläufer-Prüfung; ein Fehler ist das nicht.
    cpu_last: list[float] = field(default_factory=list)
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
    ladezeit: float = 0.0
    aussetzer: int = 0  # Stichproben ohne gerendertes Bild *nach* dem Laden
    # Mittlere CPU-Last im Messfenster, in Prozent. 0.0 heißt »nicht
    # mitgeschrieben«, nicht »Prozessor im Leerlauf« - ein Spiel mit
    # 0 % CPU-Last gibt es nicht.
    cpu_last: float = 0.0

    def __str__(self) -> str:
        text = (
            f"{self.mittel:.1f} Bilder/s im Mittel, "
            f"1-%-Tief {self.tief_1:.1f}, 0,1-%-Tief {self.tief_01:.1f} "
            f"({self.stichproben} Stichproben über {self.dauer:.0f} s)"
        )
        # Beides getrennt prüfen. In der ersten Fassung hing die Zeile mit
        # den Aussetzern an der Bedingung für die Ladezeit - lud ein Spiel
        # in unter einer Sekunde, verschwanden die Aussetzer aus der
        # Anzeige, obwohl sie gezählt waren. Am 01.10.2026 genau so
        # passiert: ein Lauf mit 49 Aussetzer-Stichproben meldete nichts.
        teile = []
        if self.ladezeit >= 1:
            teile.append(f"Ladezeit {self.ladezeit:.0f} s")
        if self.aussetzer:
            # Ein Zehntel Sekunde je Stichprobe - die übliche Schrittweite.
            teile.append(f"{self.aussetzer / 10:.1f} s Aussetzer im Spiel")
        zeile = ", dazu ".join(teile)

        # Die CPU-Last hängt nicht an »dazu«: Ladezeit und Aussetzer sind
        # Eigenschaften des Laufs, die CPU-Last ist der Hinweis darauf, ob
        # der Lauf überhaupt etwas über das Spiel aussagt. Sie wird deshalb
        # nur angehängt, nicht eingereiht.
        if self.cpu_last:
            zusatz = f"CPU-Last {self.cpu_last:.0f} %"
            zeile = f"{zeile}, {zusatz}" if zeile else zusatz
        if zeile:
            text += "\n      " + zeile
        return text


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

        # Die CPU-Last ist Beiwerk, nicht Voraussetzung: Fehlt die Spalte,
        # wird weitergelesen. Sonst hinge die ganze Messung an einer
        # MangoHud-Einstellung, die mit der Bildrate nichts zu tun hat.
        cpu_spalte = spalten.index("cpu_load") if "cpu_load" in spalten else None

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

            # Gleichlauf mit ``bilder`` ist hier Bedingung, nicht Zufall:
            # ``auswerten`` schneidet über den Index. Eine fehlende oder
            # unlesbare Zelle wird deshalb als -1 eingetragen und später
            # übersprungen, nicht weggelassen.
            if cpu_spalte is not None:
                try:
                    messung.cpu_last.append(float(zeile[cpu_spalte]))
                except (ValueError, IndexError):
                    messung.cpu_last.append(-1.0)

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


def ladezeit(messung: Messung) -> float:
    """Wie lange dauerte es bis zum ersten gerenderten Bild?

    Das ist nicht nur Beiwerk für die Auswertung, sondern eine Zahl, die
    für sich steht: Sie misst fast ausschließlich den Datenträger. Road to
    Vostok brauchte am 30.09.2026 von einer drehenden Platte 23,8 Sekunden.
    """
    for fps, sekunde in zip(messung.bilder, messung.sekunden):
        if fps >= LAEUFT_AB:
            return sekunde
    return 0.0


def auswerten(messung: Messung, aufwaermen: float = AUFWAERMEN) -> Kennzahlen | None:
    """Kennzahlen aus einem Lauf ziehen.

    Der 1-%-Tiefstwert ist hier das erste Perzentil der Bildraten – also
    der Wert, den ein Hundertstel der Stichproben unterschreitet. Er zählt
    mehr als der Mittelwert: Ruckler spürt man, einen guten Durchschnitt
    nicht.

    Gemessen wird ab dem ersten gerenderten Bild plus ``aufwaermen``. Eine
    feste Zeit ab Programmstart taugt nicht – siehe die Anmerkung bei
    ``AUFWAERMEN``.

    ``None``, wenn danach zu wenig übrig bleibt. Lieber keine Zahl als eine,
    die auf zwanzig Stichproben beruht.
    """
    beginn = ladezeit(messung) + aufwaermen

    # Über den Index, nicht über zip: Die CPU-Last muss aus demselben
    # Fenster kommen wie die Bildraten. Rechnete sie über den ganzen Lauf,
    # stünde die Ladephase mit darin - und genau dort ist die CPU-Last
    # ohnehin hoch, ganz ohne Mitläufer.
    stellen = [i for i, sekunde in enumerate(messung.sekunden) if sekunde > beginn]
    behalten = [messung.bilder[i] for i in stellen]
    verworfen = len(messung.bilder) - len(behalten)

    lasten = [messung.cpu_last[i] for i in stellen
              if i < len(messung.cpu_last) and messung.cpu_last[i] >= 0]

    # Aussetzer *nach* dem Laden bleiben in der Statistik. Sie sind kein
    # Messfehler, sondern das Unangenehmste, was ein Spiel tun kann: Bei
    # Vostok stand das Bild zwischen Sekunde 122 und 126 praktisch still.
    # Wer sie herausrechnet, macht die Zahlen schöner und die Aussage
    # wertlos.
    aussetzer = sum(1 for fps in behalten if fps < LAEUFT_AB)

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
        ladezeit=ladezeit(messung),
        aussetzer=aussetzer,
        cpu_last=sum(lasten) / len(lasten) if lasten else 0.0,
    )


def mitlaeufer_verdacht(vorher: Kennzahlen, nachher: Kennzahlen,
                        spanne: float = MITLAEUFER_SPANNE) -> str | None:
    """Liegen zwei Läufe in der CPU-Last so weit auseinander, dass der
    Vergleich nichts taugt?

    Gibt die Meldung zurück oder ``None``. SPIELRaum **sagt** es und
    verwirft nichts von selbst: Es kann der Mitläufer gewesen sein, es kann
    auch die Stelle im Spiel gewesen sein. Welches von beidem, weiß das
    Protokoll nicht - und was es nicht weiß, soll es nicht entscheiden.

    Siehe ``MITLAEUFER_SPANNE`` für die Herkunft der Zahl.
    """
    if not vorher.cpu_last or not nachher.cpu_last:
        return None  # Nicht mitgeschrieben – dann gibt es nichts zu sagen.
    # Zu kurz gemessen heißt: nichts zu sagen. Siehe MITLAEUFER_MINDESTZEIT.
    for k in (vorher, nachher):
        if k.dauer - k.ladezeit < MITLAEUFER_MINDESTZEIT:
            return None
    abstand = abs(nachher.cpu_last - vorher.cpu_last)
    if abstand < spanne:
        return None
    hoeher = "zweiten" if nachher.cpu_last > vorher.cpu_last else "ersten"
    return (f"Achtung: Die CPU-Last unterscheidet sich um {abstand:.0f} "
            f"Prozentpunkte ({vorher.cpu_last:.0f} % gegen "
            f"{nachher.cpu_last:.0f} %). Beim {hoeher} Lauf lief vermutlich "
            f"etwas mit – Bildschirmaufnahme, Fernwartung, ein zweites "
            f"Spiel. Am 12.11.2026 kostete OBS auf diesem Rechner 17 % "
            f"Bildrate, mehr als jede Einstellung je gebracht hat. Dieser "
            f"Vergleich taugt dann nicht.")


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

    # Die CPU-Last steht bewusst in derselben Tabelle wie die Bildraten,
    # nicht in einer Fußnote. Sie ist der Grund, warum die Zahlen darüber
    # womöglich nichts bedeuten - und was ein Ergebnis entwertet, gehört
    # nicht unter das Ergebnis, sondern daneben.
    if vorher.cpu_last and nachher.cpu_last:
        zeilen.append(f"  {'CPU-Last':12} {vorher.cpu_last:6.1f}  ->  "
                      f"{nachher.cpu_last:6.1f}   "
                      f"{nachher.cpu_last - vorher.cpu_last:+.1f} Punkte")
    warnung = mitlaeufer_verdacht(vorher, nachher)
    if warnung:
        # Umbruch hier und nicht beim Aufrufer: Die Warnung ist der
        # laengste Satz, den dieses Modul ausgibt, und eine Zeile ueber
        # 300 Zeichen liest im Terminal niemand.
        zeilen.extend(textwrap.wrap(warnung, width=74,
                                    initial_indent="  ",
                                    subsequent_indent="  "))
    return zeilen
