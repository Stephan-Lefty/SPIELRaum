"""Was findet SPIELRaum auf diesem Rechner vor?

Dieses Modul ist die Antwort auf eine Anforderung, die von Anfang an feststand:
SPIELRaum soll auf Manjaro **und** auf Debian 13 laufen. Die Versuchung ist
groß, Pfade und Werkzeuge einfach hinzuschreiben – sie stimmen ja auf dem
eigenen Rechner. Genau daran scheitern Programme dann auf dem fremden.

Deshalb gilt hier durchgehend: **nachsehen, nicht annehmen.** Kein Modul in
SPIELRaum ruft ein Werkzeug direkt auf; alle fragen hier nach, ob es da ist.
Fehlt eines, ist das kein Absturz, sondern eine Stellschraube, die ausfällt –
und der Anwender erfährt, welche und warum.

Die bekannten Unterschiede zwischen den beiden Zielsystemen:

    Werkzeug           Arch/Manjaro          Debian 13
    ---------------------------------------------------------------
    gamemoderun        Paket gamemode        Paket gamemode
    mangohud           Paket mangohud        Paket mangohud
    cpupower           Paket cpupower        linux-cpupower
    powerprofilesctl   power-profiles-daemon power-profiles-daemon
    nvidia-smi         nvidia-utils          nvidia-smi

Die Paketnamen stehen hier nur als Gedächtnisstütze für die Fehlermeldungen.
Verlassen tut sich der Code darauf nicht – er sucht die Programme im ``PATH``.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

# Zu welchem Paket gehört ein fehlendes Werkzeug? Fließt ausschließlich in
# Fehlermeldungen ein, damit dort nicht »gamemoderun fehlt« steht, sondern
# der Befehl, mit dem man es bekommt.
PAKETE: dict[str, dict[str, str]] = {
    "gamemoderun": {"arch": "gamemode", "debian": "gamemode"},
    "mangohud": {"arch": "mangohud", "debian": "mangohud"},
    "cpupower": {"arch": "cpupower", "debian": "linux-cpupower"},
    "powerprofilesctl": {"arch": "power-profiles-daemon", "debian": "power-profiles-daemon"},
    "nvidia-smi": {"arch": "nvidia-utils", "debian": "nvidia-smi"},
}


@dataclass(frozen=True)
class Umgebung:
    """Der Befund über diesen Rechner. Einmal ermittelt, dann unveränderlich."""

    familie: str  # "arch", "debian" oder "unbekannt"
    name: str  # was /etc/os-release als PRETTY_NAME führt
    werkzeuge: dict[str, str | None] = field(default_factory=dict)

    def hat(self, werkzeug: str) -> bool:
        return self.werkzeuge.get(werkzeug) is not None

    def pfad(self, werkzeug: str) -> str | None:
        return self.werkzeuge.get(werkzeug)

    def fehlt_hinweis(self, werkzeug: str) -> str:
        """Ein Satz, der nicht nur meldet, was fehlt, sondern wie man es bekommt."""
        paket = PAKETE.get(werkzeug, {}).get(self.familie)
        if paket is None:
            return f"»{werkzeug}« ist nicht installiert."
        if self.familie == "arch":
            return f"»{werkzeug}« fehlt. Nachinstallieren mit: sudo pacman -S {paket}"
        if self.familie == "debian":
            return f"»{werkzeug}« fehlt. Nachinstallieren mit: sudo apt install {paket}"
        return f"»{werkzeug}« fehlt (Paket: {paket})."


def _os_release() -> dict[str, str]:
    """``/etc/os-release`` einlesen. Fehlt die Datei, ist das kein Grund zum Abbruch."""
    werte: dict[str, str] = {}
    try:
        text = Path("/etc/os-release").read_text(encoding="utf-8")
    except OSError:
        return werte
    for zeile in text.splitlines():
        if "=" not in zeile or zeile.startswith("#"):
            continue
        schluessel, _, wert = zeile.partition("=")
        werte[schluessel.strip()] = wert.strip().strip('"').strip("'")
    return werte


def _familie(werte: dict[str, str]) -> str:
    """Arch oder Debian?

    ``ID_LIKE`` ist hier wichtiger als ``ID``: Manjaro meldet sich als
    ``manjaro`` mit ``ID_LIKE=arch``, Linux Mint als ``linuxmint`` mit
    ``ID_LIKE=ubuntu debian``. Wer nur ``ID`` prüft, unterstützt genau zwei
    Distributionen statt zweier Familien.
    """
    kennungen = {werte.get("ID", "").lower()}
    kennungen.update(werte.get("ID_LIKE", "").lower().split())
    if kennungen & {"arch", "archlinux", "manjaro"}:
        return "arch"
    if kennungen & {"debian", "ubuntu"}:
        return "debian"
    return "unbekannt"


@lru_cache(maxsize=1)
def ermitteln() -> Umgebung:
    """Den Rechner einmal befragen und das Ergebnis behalten."""
    werte = _os_release()
    werkzeuge = {name: shutil.which(name) for name in PAKETE}
    return Umgebung(
        familie=_familie(werte),
        name=werte.get("PRETTY_NAME", "unbekanntes System"),
        werkzeuge=werkzeuge,
    )


# --- Verzeichnisse ----------------------------------------------------------
#
# Alles nach XDG. Fest verdrahtete ``~/.config``-Pfade brechen, sobald jemand
# XDG_CONFIG_HOME setzt – und unter Flatpak-Steam ist das der Normalfall.


def konfig_verzeichnis() -> Path:
    """Wo die Profile liegen: ``~/.config/spielraum``."""
    wurzel = os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config"
    return Path(wurzel) / "spielraum"


def daten_verzeichnis() -> Path:
    """Wo Messungen und Sicherungen liegen: ``~/.local/share/spielraum``."""
    wurzel = os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share"
    return Path(wurzel) / "spielraum"


def platte_dreht(pfad: Path) -> bool | None:
    """Liegt dieser Pfad auf einer drehenden Platte?

    ``None`` heißt: nicht feststellbar. Das ist kein Randfall – bei
    Netzlaufwerken, im Container und auf manchen RAID-Verbünden gibt es die
    Auskunft schlicht nicht, und dann ist Schweigen ehrlicher als ein
    geratenes »nein«.

    Der Weg führt über die Geräte-Nummer aus ``stat``: Sie zeigt auf einen
    Eintrag unter ``/sys/dev/block``, und dort steht ``queue/rotational``.
    Bei einer Partition liegt die Angabe eine Ebene höher, beim Gerät selbst –
    deshalb die zweite Stelle, an der nachgesehen wird.

    Warum das hier steht: Ein Spiel auf einer 7200er-Platte ruckelt beim
    Nachladen, und keine Einstellung der Welt ändert daran etwas. SPIELRaum
    soll das sagen können, statt am falschen Ende zu schrauben.
    """
    try:
        angaben = os.stat(pfad)
    except OSError:
        return None

    block = Path(f"/sys/dev/block/{os.major(angaben.st_dev)}:{os.minor(angaben.st_dev)}")
    for kandidat in (block / "queue" / "rotational", block / ".." / "queue" / "rotational"):
        try:
            return kandidat.read_text().strip() == "1"
        except OSError:
            continue
    return None


def laufzeit_verzeichnis() -> Path:
    """Wo das Journal des laufenden Spiels liegt.

    ``XDG_RUNTIME_DIR`` (meist ``/run/user/1000``) wird beim Abmelden geleert.
    Das ist hier **erwünscht**: Ein Journal, das einen Neustart überlebt,
    beschreibt einen Zustand, den es nicht mehr gibt.

    Fehlt die Variable – etwa in einer ``cron``-Umgebung –, weichen wir auf das
    Datenverzeichnis aus. Dann bleibt das Journal zwar liegen, aber der
    Anlaufschutz in ``zustand.py`` erkennt das am Zeitstempel.
    """
    wurzel = os.environ.get("XDG_RUNTIME_DIR")
    if wurzel:
        return Path(wurzel) / "spielraum"
    return daten_verzeichnis() / "laufzeit"
