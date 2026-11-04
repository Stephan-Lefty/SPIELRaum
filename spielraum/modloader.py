"""Den Mod Loader eines Spiels aktuell halten.

Der Anlass, 04.11.2026: Road to Vostok läuft mit dem Vostok Mod Loader, und
der hält **die Mods** von selbst aktuell – Reiter »Updates«, Knopf, fertig.
Sich selbst hält er nicht aktuell. Er prüft nur und bietet »Open Page« an,
das eine Webseite im Browser öffnet; herunterladen und einbauen ist
Handarbeit. Folge auf diesem Rechner: Fassung 3.2.1 im Einsatz, während seit
dem 06.10.2026 v3.4.2 veröffentlicht war – ein Monat Rückstand, einfach
weil der Weg über eine Webseite führt.

Das ist die Lücke, die SPIELRaum füllt. Alles andere am Mod-Wesen bleibt beim
Mod Loader; siehe die Regel »Was nicht nachgebaut wird« in CLAUDE.md.

## Prüfen und holen von selbst, einbauen auf Knopfdruck

Herunterladen ist harmlos – es landet in einem Zwischenlager und ändert am
Spiel nichts. Einbauen ist es nicht: Bei einem Fassungswechsel verwirft der
Mod Loader seinen Hook-Zwischenspeicher, löscht seinen Zustand und setzt die
``override.cfg`` zurück (``_static_reset_override_cfg`` in modloader.gd).
Eine neue Fassung kann damit das Zusammenspiel mit den installierten Mods
verändern – und das soll niemanden in der Sekunde überraschen, in der er
spielen wollte. Deshalb die Teilung.

## Warum die Quelle hier im Code steht und nicht im Profil

Ein Profil ist eine Datei, die jeder bearbeiten kann. Stünde dort eine
Adresse, aus der SPIELRaum eine Datei ins Spielverzeichnis lädt, wäre das
eine Einladung – dieselbe Überlegung wie bei der Tastenbelegung, siehe die
Sicherheitsregel in CLAUDE.md. Das Profil nennt deshalb nur eine **Kennung**
aus ``QUELLEN``; wohin sie zeigt, entscheidet das Programm.

## Kein Journaleintrag

Das Journal in ``zustand.py`` beschreibt, was für *einen Spielstart*
verstellt wurde, und wird beim Beenden zurückgenommen. Ein eingebauter Mod
Loader soll aber bleiben. Stünde er im Journal, würde ihn das Aufräumen nach
einem Absturz wieder entfernen – ein Update, das sich selbst zurücknimmt.
Die Rücknahme läuft deshalb über die Sicherung daneben, nicht über das
Journal.
"""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from . import stellschrauben, umgebung

# Wie lange auf das Netz gewartet wird. Kurz gehalten: Die Abfrage darf den
# Anwender nie aufhalten, und eine Fassungsnummer ist nichts, worauf man
# wartet.
ZEITGRENZE = 15

# Eine Datei unter dieser Größe ist keine modloader.gd. Die Fassung 3.2.1 hat
# 637 KB; die Grenze liegt bewusst weit darunter, damit sie nicht bei jeder
# Veröffentlichung nachgezogen werden muss. Sie fängt den Fall ab, dass eine
# Fehlerseite oder eine leere Antwort im Spielordner landet.
MINDESTGROESSE = 50_000


@dataclass(frozen=True)
class Quelle:
    """Woher ein Mod Loader kommt und wie man ihm seine Fassung ansieht."""

    kennung: str
    name: str
    repo: str          # GitHub, »Eigner/Name«
    datei: str         # wie die Datei im Spielordner heißt
    muster: str        # findet die Fassung im Dateitext

    @property
    def fassungs_url(self) -> str:
        return f"https://api.github.com/repos/{self.repo}/releases/latest"

    @property
    def datei_url(self) -> str:
        return (f"https://github.com/{self.repo}/releases/latest/download/"
                f"{self.datei}")


# Die bekannten Quellen. Erweitert wird hier, nicht im Profil.
QUELLEN: dict[str, Quelle] = {
    "vostok": Quelle(
        kennung="vostok",
        name="Road to Vostok Mod Loader",
        repo="ametrocavich/vostok-mod-loader",
        datei="modloader.gd",
        # In modloader.gd steht: MODLOADER_VERSION := "3.2.1"
        muster=r'MODLOADER_VERSION\s*:?=\s*"([^"]+)"',
    ),
}


class ModLoaderFehler(RuntimeError):
    """Etwas ging nicht – mit einem Satz, der weiterhilft."""


@dataclass
class Stand:
    """Was SPIELRaum über diesen Mod Loader weiß."""

    quelle: Quelle
    ziel: Path
    installiert: str | None = None
    neueste: str | None = None
    bereit: Path | None = None   # heruntergeladen und wartet
    grund: str = ""              # warum nicht geprüft werden konnte

    @property
    def veraltet(self) -> bool:
        if not self.installiert or not self.neueste:
            return False
        return vergleichen(self.neueste, self.installiert) > 0

    @property
    def vorhanden(self) -> bool:
        return self.installiert is not None


# --- Fassungen -------------------------------------------------------------


def fassung_aus_text(quelle: Quelle, text: str) -> str | None:
    """Die Fassung aus dem Dateitext lesen.

    Aus der Datei selbst, nicht aus einem Dateinamen oder einer Notiz
    daneben: Der Dateiname sagt nichts darüber, was wirklich installiert
    ist, und eine Notiz kann veralten. Die Datei kann es nicht.
    """
    treffer = re.search(quelle.muster, text)
    return treffer.group(1).strip() if treffer else None


def installierte_fassung(quelle: Quelle, ziel: Path) -> str | None:
    """Welche Fassung liegt gerade im Spielordner?"""
    if not ziel.is_file():
        return None
    try:
        # Die Fassung steht in den ersten Zeilen; die ganze Datei zu lesen
        # wären 637 KB für eine Zeichenkette.
        with ziel.open("r", encoding="utf-8", errors="replace") as datei:
            kopf = datei.read(8192)
    except OSError:
        return None
    return fassung_aus_text(quelle, kopf)


def vergleichen(a: str, b: str) -> int:
    """Zwei Fassungen vergleichen: >0 wenn ``a`` neuer ist.

    Punktweise und nach Zahlenwert, nicht als Text – sonst wäre »3.10.0«
    älter als »3.9.0«, weil »1« vor »9« kommt. Ein führendes »v« wird
    abgeschnitten: GitHub markiert die Veröffentlichung als ``v3.4.2``,
    in der Datei steht ``3.4.2``.
    """
    def teile(s: str) -> list[int]:
        s = s.strip().lstrip("vV")
        heraus: list[int] = []
        for stueck in re.split(r"[.\-+]", s):
            ziffern = re.match(r"\d+", stueck)
            if ziffern is None:
                break
            heraus.append(int(ziffern.group(0)))
        return heraus

    links, rechts = teile(a), teile(b)
    laenge = max(len(links), len(rechts))
    links += [0] * (laenge - len(links))
    rechts += [0] * (laenge - len(rechts))
    return (links > rechts) - (links < rechts)


# --- Das Netz --------------------------------------------------------------


def _holen(url: str) -> bytes:
    """Eine Adresse abrufen. Fehler werden zu einem lesbaren Satz."""
    anfrage = urllib.request.Request(
        url,
        headers={"User-Agent": "SPIELRaum", "Accept": "*/*"},
    )
    try:
        with urllib.request.urlopen(anfrage, timeout=ZEITGRENZE) as antwort:
            return antwort.read()
    except urllib.error.HTTPError as fehler:
        raise ModLoaderFehler(
            f"{url} antwortete mit {fehler.code}. "
            "Vielleicht gibt es dort keine Veröffentlichung mehr."
        ) from fehler
    except (urllib.error.URLError, OSError, TimeoutError) as fehler:
        raise ModLoaderFehler(f"Kein Zugriff auf {url}: {fehler}") from fehler


def neueste_fassung(quelle: Quelle) -> str:
    """Die neueste veröffentlichte Fassung – über die GitHub-Schnittstelle."""
    roh = _holen(quelle.fassungs_url)
    try:
        daten = json.loads(roh)
    except json.JSONDecodeError as fehler:
        raise ModLoaderFehler(
            "Die Antwort von GitHub war keine gültige Auskunft."
        ) from fehler
    marke = str(daten.get("tag_name", "")).strip()
    if not marke:
        raise ModLoaderFehler("GitHub nennt keine Fassung für diese Quelle.")
    return marke.lstrip("vV")


# --- Zwischenlager ---------------------------------------------------------


def zwischenlager() -> Path:
    """Wohin heruntergeladen wird, bevor es eingebaut wird.

    Nicht in den Spielordner: Eine Datei dort gilt als eingebaut. Solange
    nichts bestätigt ist, hat sie im Spiel nichts zu suchen.
    """
    return umgebung.daten_verzeichnis() / "modloader"


def _lagerpfad(quelle: Quelle, fassung: str) -> Path:
    return zwischenlager() / f"{quelle.kennung}-{fassung}-{quelle.datei}"


def bereitliegend(quelle: Quelle, fassung: str) -> Path | None:
    """Liegt diese Fassung schon heruntergeladen da?"""
    pfad = _lagerpfad(quelle, fassung)
    if not pfad.is_file() or pfad.stat().st_size < MINDESTGROESSE:
        return None
    return pfad


def herunterladen(quelle: Quelle, fassung: str) -> Path:
    """Die Datei ins Zwischenlager holen und prüfen, dass sie es ist.

    Geprüft wird nicht nur, *dass* etwas ankam, sondern dass es die
    erwartete Fassung ist: In der Datei muss dieselbe Nummer stehen, die
    GitHub als Veröffentlichung nennt. Das fängt eine Fehlerseite, eine
    halbe Übertragung und eine Veröffentlichung ab, deren Anhang nicht zu
    ihrer Marke passt.
    """
    if (schon_da := bereitliegend(quelle, fassung)) is not None:
        return schon_da

    roh = _holen(quelle.datei_url)
    if len(roh) < MINDESTGROESSE:
        raise ModLoaderFehler(
            f"Die heruntergeladene Datei ist nur {len(roh)} Bytes groß – das "
            f"ist keine {quelle.datei}. Nichts eingebaut."
        )

    text = roh.decode("utf-8", errors="replace")
    gefunden = fassung_aus_text(quelle, text)
    if gefunden is None:
        raise ModLoaderFehler(
            f"In der heruntergeladenen {quelle.datei} steht keine "
            "Fassungsnummer. Nichts eingebaut."
        )
    if vergleichen(gefunden, fassung) != 0:
        raise ModLoaderFehler(
            f"GitHub nennt die Veröffentlichung »{fassung}«, in der Datei "
            f"steht aber »{gefunden}«. Nichts eingebaut."
        )

    lager = _lagerpfad(quelle, fassung)
    stellschrauben.atomar_schreiben(lager, text)
    return lager


# --- Stand und Einbau ------------------------------------------------------


def stand_lokal(quelle: Quelle, ziel: Path) -> Stand:
    """Was ohne Netz zu sehen ist: installierte Fassung, Zwischenlager.

    Dafür gebaut, dass die Oberfläche etwas anzeigen kann, ohne auf eine
    Antwort aus dem Netz zu warten.
    """
    ergebnis = Stand(quelle=quelle, ziel=ziel,
                     installiert=installierte_fassung(quelle, ziel))
    neuestes: tuple[str, Path] | None = None
    lager = zwischenlager()
    if lager.is_dir():
        for pfad in lager.glob(f"{quelle.kennung}-*-{quelle.datei}"):
            fassung = pfad.name[len(quelle.kennung) + 1:-len(quelle.datei) - 1]
            if neuestes is None or vergleichen(fassung, neuestes[0]) > 0:
                neuestes = (fassung, pfad)
    if neuestes is not None:
        ergebnis.neueste = neuestes[0]
        ergebnis.bereit = neuestes[1]
    return ergebnis


def pruefen(quelle: Quelle, ziel: Path, laden: bool = True) -> Stand:
    """Nachsehen, ob es etwas Neueres gibt – und es gleich holen.

    Ein Fehler aus dem Netz wird **nicht** geworfen, sondern in ``grund``
    hinterlegt. Diese Funktion läuft im Hintergrund eines Spielstarts; ein
    Ausnahmefehler dort hätte nichts mit dem Spiel zu tun und würde ihn
    trotzdem beenden.
    """
    ergebnis = stand_lokal(quelle, ziel)
    try:
        ergebnis.neueste = neueste_fassung(quelle)
        if laden and ergebnis.veraltet:
            ergebnis.bereit = herunterladen(quelle, ergebnis.neueste)
        elif not ergebnis.veraltet:
            ergebnis.bereit = None
    except ModLoaderFehler as fehler:
        ergebnis.grund = str(fehler)
    return ergebnis


def _sicherungsname(quelle: Quelle, fassung: str) -> str:
    return f"{quelle.datei}.{fassung}-{time.strftime('%Y%m%d-%H%M%S')}"


def einbauen(quelle: Quelle, ziel: Path, fassung: str,
             sicherungsordner: Path) -> list[str]:
    """Die heruntergeladene Fassung in den Spielordner übernehmen.

    Reihenfolge: erst die alte Datei zur Seite, dann die neue hin. Und die
    neue atomar, also daneben schreiben und umbenennen – eine halb
    geschriebene ``modloader.gd`` wäre ein Spiel, das nicht mehr startet.
    """
    bereit = bereitliegend(quelle, fassung)
    if bereit is None:
        raise ModLoaderFehler(
            f"Fassung {fassung} liegt nicht im Zwischenlager. Erst prüfen."
        )

    bericht: list[str] = []
    alt = installierte_fassung(quelle, ziel)
    if ziel.is_file():
        sicherungsordner.mkdir(parents=True, exist_ok=True)
        sicherung = sicherungsordner / _sicherungsname(quelle, alt or "unbekannt")
        sicherung.write_bytes(ziel.read_bytes())
        bericht.append(f"Alte Fassung gesichert: {sicherung}")
    elif not ziel.parent.is_dir():
        raise ModLoaderFehler(
            f"{ziel.parent} gibt es nicht – ist das Spiel installiert?"
        )

    stellschrauben.atomar_schreiben(
        ziel, bereit.read_text(encoding="utf-8", errors="replace"))
    bericht.append(f"{quelle.name}: {alt or 'nichts'} → {fassung}")
    return bericht


def sicherungen(quelle: Quelle, sicherungsordner: Path) -> list[Path]:
    """Die zur Seite gelegten Fassungen, neueste zuerst."""
    if not sicherungsordner.is_dir():
        return []
    return sorted(sicherungsordner.glob(f"{quelle.datei}.*"),
                  key=lambda p: p.name, reverse=True)


def zuruecknehmen(quelle: Quelle, ziel: Path,
                  sicherungsordner: Path) -> list[str]:
    """Die zuletzt gesicherte Fassung wieder einbauen.

    Nicht über das Journal, siehe den Modulkopf: Ein eingebauter Mod Loader
    soll bleiben, bis jemand es anders will.
    """
    vorhanden = sicherungen(quelle, sicherungsordner)
    if not vorhanden:
        raise ModLoaderFehler(
            "Es liegt keine gesicherte Fassung – nichts zurückzunehmen."
        )
    zurueck = vorhanden[0]
    text = zurueck.read_text(encoding="utf-8", errors="replace")
    war = installierte_fassung(quelle, ziel)
    stellschrauben.atomar_schreiben(ziel, text)
    return [f"{quelle.name}: {war or 'nichts'} → "
            f"{fassung_aus_text(quelle, text) or '?'} (aus {zurueck.name})"]
