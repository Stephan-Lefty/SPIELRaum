"""Tastenbelegung pro Spiel – über keyd, auf Zeit.

Der Anlass: Wer die Maus links führt, erreicht mit der rechten Hand nur den
Bereich rechts von I/K/M. Spiele legen ihre Befehle aber auf WASD, Leertaste
und die linke Umschalttaste – alles unter der *linken* Hand. Jedes Spiel
einzeln umzustellen hilft nur begrenzt: Manche bieten es gar nicht an, und
bei jedem neuen Spiel fängt die Arbeit von vorn an.

``keyd`` setzt Tasten auf Systemebene um, und zwar **pro Gerät**. Damit lässt
sich eine Spieltastatur umbelegen, ohne die Arbeitstastatur anzurühren.

**Warum auf Zeit und nicht dauerhaft?** Am 23.10.2026 lag die Belegung erst
fest in ``/etc/keyd/``. Dann schrieb die Pfeiltaste auch im Browser ein »w«.
Eine Übersetzung, die immer gilt, ist keine Spieleinstellung, sondern ein
neues Tastaturlayout. Deshalb setzt SPIELRaum sie beim Spielstart und nimmt
sie beim Beenden zurück – dasselbe Versprechen wie bei allem anderen hier.

**Warum ohne root?** keyd legt einen Socket unter ``/run/keyd.socket`` an,
der der Gruppe ``keyd`` gehört. Wer in dieser Gruppe ist, darf dem laufenden
Dienst Belegungen schicken. Kein Polkit, kein Passwortdialog, kein
``sudo`` – und vor allem: SPIELRaum braucht selbst keine erhöhten Rechte.
Die Gruppe wird einmalig vergeben, siehe ``docs/tasten.md``.
"""

from __future__ import annotations

import re
import subprocess
from functools import lru_cache

from . import umgebung
from .zustand import Journal

# Die Stellschraube, unter der die Belegung im Journal steht. Ein eigener
# Name, weil das Zurücksetzen hier anders läuft als bei Dateien: Es gibt
# keine Sicherungskopie, sondern einen Befehl, der alles zurückdreht.
STELLSCHRAUBE = "tasten"

# Ebenen, die keyd von Haus aus kennt. Sie dürfen als Ziel stehen, damit
# Umschalt und Strg sich wie echte Modifikatoren verhalten und nicht nur
# ihren Tastencode schicken – beim Sprinten hält man die Taste und bewegt
# sich gleichzeitig.
EBENEN = {"shift", "control", "alt", "altgr", "meta", "layer"}

_EBENE = re.compile(r"^layer\(([a-z]+)\)$")


class TastenFehler(RuntimeError):
    """Etwas an der Tastenbelegung stimmt nicht – mit einem Satz, der weiterhilft."""


@lru_cache(maxsize=1)
def bekannte_tasten() -> frozenset[str]:
    """Alle Tastennamen, die keyd kennt.

    Wird gegen die Profilwerte geprüft. Ein Profil ist eine Datei, die jeder
    bearbeiten kann; was daraus in einen Aufruf wandert, muss gegen eine
    feste Liste laufen. Siehe die Sicherheitsregel in CLAUDE.md.
    """
    umg = umgebung.ermitteln()
    pfad = umg.pfad("keyd")
    if pfad is None:
        return frozenset()
    try:
        fertig = subprocess.run([pfad, "list-keys"], capture_output=True,
                                text=True, timeout=5, check=False)
    except (OSError, subprocess.SubprocessError):
        return frozenset()
    return frozenset(fertig.stdout.split())


def pruefen(belegung: dict[str, str]) -> list[str]:
    """Jede Zuordnung gegen die Liste prüfen, die keyd selbst ausgibt.

    Gibt die Beanstandungen zurück, nicht nur »ungültig«: Wer eine Taste
    falsch schreibt, will wissen welche.
    """
    gueltig = bekannte_tasten()
    if not gueltig:
        # Ohne keyd lässt sich nichts prüfen. Dann auch nichts setzen –
        # das fängt der Aufrufer über ``verfuegbar()`` ab.
        return []

    beanstandet: list[str] = []
    for taste, ziel in belegung.items():
        if taste not in gueltig:
            beanstandet.append(f"»{taste}« ist keine Taste, die keyd kennt")
        treffer = _EBENE.match(ziel)
        if treffer:
            if treffer.group(1) not in EBENEN:
                beanstandet.append(
                    f"»{ziel}«: Ebene unbekannt, erlaubt sind "
                    + ", ".join(sorted(EBENEN))
                )
        elif ziel not in gueltig:
            beanstandet.append(f"»{ziel}« ist keine Taste, die keyd kennt")
    return beanstandet


def verfuegbar() -> tuple[bool, str]:
    """Kann SPIELRaum Tasten umlegen? Und wenn nicht, woran liegt es?

    Drei Dinge müssen stimmen, und jedes hat eine eigene Abhilfe. Eine
    pauschale Meldung »geht nicht« würde den Anwender im Regen stehen
    lassen.
    """
    umg = umgebung.ermitteln()
    if not umg.hat("keyd"):
        return False, umg.fehlt_hinweis("keyd")

    if not _dienst_laeuft():
        return False, (
            "Der keyd-Dienst läuft nicht. Starten mit: "
            "sudo systemctl enable --now keyd"
        )

    erreichbar, grund = _socket_erreichbar()
    if not erreichbar:
        return False, grund

    return True, "keyd ist bereit."


def _dienst_laeuft() -> bool:
    """Läuft der Dienst? Über systemctl, nicht über eine Prozessliste.

    ``pgrep keyd`` würde auch bei einem von Hand gestarteten keyd anschlagen,
    das gleich wieder weg ist.
    """
    try:
        fertig = subprocess.run(["systemctl", "is-active", "keyd"],
                                capture_output=True, text=True, timeout=5,
                                check=False)
    except (OSError, subprocess.SubprocessError):
        return False
    return fertig.stdout.strip() == "active"


def _socket_erreichbar() -> tuple[bool, str]:
    """Darf dieser Benutzer dem Dienst etwas schicken?

    Geprüft wird durch Ausprobieren statt durch Nachrechnen über
    Gruppenlisten: ``id`` zeigt die Gruppen der *Anmeldung*, und eine frisch
    vergebene Gruppe steht dort erst nach dem nächsten Anmelden. Ein
    harmloser Aufruf sagt die Wahrheit.
    """
    umg = umgebung.ermitteln()
    pfad = umg.pfad("keyd")
    if pfad is None:
        return False, "keyd ist nicht installiert."
    try:
        fertig = subprocess.run([pfad, "bind", "reset"], capture_output=True,
                                text=True, timeout=5, check=False)
    except (OSError, subprocess.SubprocessError) as fehler:
        return False, f"keyd ließ sich nicht aufrufen: {fehler}"

    if fertig.returncode == 0:
        return True, ""

    meldung = (fertig.stderr or fertig.stdout).strip()
    if "permission" in meldung.lower() or "socket" in meldung.lower():
        return False, (
            "Kein Zugriff auf /run/keyd.socket. Einmalig einrichten mit: "
            "sudo usermod -aG keyd $USER — danach ab- und wieder anmelden."
        )
    return False, f"keyd meldet: {meldung}"


def setzen(belegung: dict[str, str], journal: Journal) -> list[str]:
    """Die Belegung dieses Spiels an keyd schicken.

    Der Journaleintrag entsteht **vor** dem Aufruf. Bricht SPIELRaum
    zwischen beiden Schritten ab, findet der nächste Start den Eintrag und
    setzt zurück – lieber einmal zu viel zurückgesetzt als eine Tastatur,
    die bis zum Neustart falsch schreibt.
    """
    if not belegung:
        return []

    beanstandet = pruefen(belegung)
    if beanstandet:
        raise TastenFehler(
            "Die Tastenbelegung im Profil stimmt nicht:\n  - "
            + "\n  - ".join(beanstandet)
        )

    bereit, grund = verfuegbar()
    if not bereit:
        raise TastenFehler(grund)

    # »vorher« ist hier kein Wert, sondern die Zusage, dass vorher nichts
    # gesetzt war: Die Datei unter /etc/keyd legt bewusst keine Taste um.
    # Zurückgesetzt wird deshalb mit »reset«, nicht mit einem alten Wert.
    journal.vermerken(STELLSCHRAUBE, "keyd", None, nachher=_als_text(belegung))

    pfad = umgebung.ermitteln().pfad("keyd")
    argumente = [f"{taste}={ziel}" for taste, ziel in belegung.items()]
    fertig = subprocess.run([pfad, "bind", *argumente], capture_output=True,
                            text=True, timeout=10, check=False)
    if fertig.returncode != 0:
        raise TastenFehler(
            "keyd hat die Belegung abgelehnt: "
            + (fertig.stderr or fertig.stdout).strip()
        )

    return [f"{taste} → {ziel}" for taste, ziel in belegung.items()]


def zuruecknehmen() -> str:
    """Alles zurück auf das, was in ``/etc/keyd`` steht.

    ``keyd bind reset`` verwirft sämtliche zur Laufzeit gesetzten Belegungen.
    Weil die Datei dort keine Taste umlegt, ist die Tastatur danach wieder
    das, was auf ihren Tasten steht.
    """
    umg = umgebung.ermitteln()
    pfad = umg.pfad("keyd")
    if pfad is None:
        return "keyd ist nicht installiert – nichts zurückzunehmen."
    try:
        fertig = subprocess.run([pfad, "bind", "reset"], capture_output=True,
                                text=True, timeout=10, check=False)
    except (OSError, subprocess.SubprocessError) as fehler:
        return f"FEHLER beim Zurücksetzen der Tasten: {fehler}"
    if fertig.returncode != 0:
        return "FEHLER beim Zurücksetzen der Tasten: " + (
            fertig.stderr or fertig.stdout).strip()
    return "Tastenbelegung zurückgenommen"


def _als_text(belegung: dict[str, str]) -> str:
    """Für das Journal: eine Zeile, die ein Mensch lesen kann."""
    return " ".join(f"{t}={z}" for t, z in sorted(belegung.items()))
