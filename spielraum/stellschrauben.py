"""Was SPIELRaum für ein Spiel verstellt – und wie es das zurücknimmt.

Jede Stellschraube hier erfüllt zwei Bedingungen. Erstens: Sie braucht keine
Systemrechte. Was Rechte braucht – Taktregler, GPU-Modus, Prozesspriorität –
macht GameMode, und der hat dafür einen geprüften Dienst. Zweitens: Sie
schreibt ihren alten Zustand ins Journal, **bevor** sie etwas ändert.

Die zweite Bedingung ist der Grund, warum dieses Modul nicht einfach ein paar
``os.environ``-Zuweisungen ist. Ein Programm, das erst ändert und sich dann
merkt, verliert bei einem Absturz dazwischen genau die Information, die es
zum Aufräumen bräuchte.

**Ein Kniff, der viel Zustand spart:** Zwei der wirksamsten Stellschrauben
sind gar keine. Sowohl GameMode als auch die Sperre gegen Bildschirmschoner
und Ruhezustand sind *Wrapper* – Programme, die das Spiel starten und deren
Wirkung endet, wenn der Prozess endet. Da gibt es nichts zurückzusetzen, weil
nie etwas dauerhaft verstellt wurde. Was sich nicht verstellen lässt, kann
auch nicht hängenbleiben.
"""

from __future__ import annotations

import os
import shutil
import time
from pathlib import Path

from . import godot_cfg, umgebung
from .profil import Profil
from .zustand import Journal


def sicherungsordner(app_id: int | None, name: str) -> Path:
    kennung = str(app_id) if app_id else "".join(
        z if z.isalnum() else "_" for z in name
    )
    return umgebung.daten_verzeichnis() / "sicherungen" / kennung


def messordner() -> Path:
    return umgebung.daten_verzeichnis() / "messungen"


# --- Umgebung ---------------------------------------------------------------


def umgebung_bauen(profil: Profil, messen_in: Path | None = None) -> dict[str, str]:
    """Die Umgebung für das Spiel zusammenstellen.

    Wichtig: Es wird eine **Kopie** aufgebaut und dem Kindprozess mitgegeben,
    nicht ``os.environ`` des laufenden SPIELRaum verändert. Damit kann diese
    Stellschraube gar nicht hängenbleiben – der Elternprozess bleibt, wie er
    war, und mit ihm jede andere Anwendung.
    """
    werte = dict(os.environ)
    werte.update(profil.variablen)

    if profil.mangohud and umgebung.ermitteln().hat("mangohud"):
        werte["MANGOHUD"] = "1"
        if messen_in is not None:
            messen_in.mkdir(parents=True, exist_ok=True)
            # autostart_log zeichnet ab der ersten Sekunde auf; ohne das
            # müsste man im Spiel eine Taste drücken, und dann misst man
            # Sitzungen unterschiedlicher Länge gegeneinander.
            werte["MANGOHUD_CONFIG"] = ",".join([
                f"output_folder={messen_in}",
                "autostart_log=1",
                "log_interval=100",
                "fps_limit=0",
            ])
    return werte


def befehl_umhuellen(profil: Profil, befehl: list[str]) -> list[str]:
    """GameMode und die Ruhesperre vor den Spielbefehl setzen.

    Reihenfolge von außen nach innen::

        systemd-inhibit  gamemoderun  <Spiel>

    ``systemd-inhibit`` zuerst, weil seine Sperre für alles darunter gelten
    soll. Beide sind Wrapper: Endet das Spiel, endet ihre Wirkung – ohne dass
    jemand etwas zurücksetzen müsste.
    """
    umg = umgebung.ermitteln()
    voll = list(befehl)

    if profil.gamemode and umg.hat("gamemoderun"):
        voll = [umg.pfad("gamemoderun"), *voll]

    if profil.nicht_stoeren and umg.hat("systemd-inhibit"):
        voll = [
            umg.pfad("systemd-inhibit"),
            "--what=idle:sleep",
            f"--why=SPIELRaum: {profil.name} läuft",
            "--mode=block",
            "--",
            *voll,
        ]
    return voll


# --- Dateien ----------------------------------------------------------------


def _pfad_aufloesen(vorlage: str, spielordner: Path | None, praefix: Path | None) -> Path:
    """``{spielordner}/override.cfg`` in einen echten Pfad übersetzen."""
    if "{spielordner}" in vorlage:
        if spielordner is None:
            raise FileNotFoundError(
                "Das Profil verweist auf {spielordner}, aber das Spiel ist "
                "nicht auffindbar – vermutlich ist es nicht installiert."
            )
        vorlage = vorlage.replace("{spielordner}", str(spielordner))
    if "{praefix}" in vorlage:
        if praefix is None:
            raise FileNotFoundError(
                "Das Profil verweist auf {praefix}, aber es gibt kein "
                "Proton-Präfix – läuft das Spiel nativ?"
            )
        vorlage = vorlage.replace("{praefix}", str(praefix))
    return Path(vorlage)


def dateien_anwenden(
    profil: Profil,
    journal: Journal,
    spielordner: Path | None = None,
    praefix: Path | None = None,
) -> list[str]:
    """Die Einstellungsdateien des Spiels anpassen – jede mit Sicherung.

    Gibt zurück, was getan wurde, damit der Anwender es liest, statt es zu
    erraten. Die Sicherung wird mit ``shutil.copy2`` angelegt, also samt
    Zeitstempeln: Manche Spiele entscheiden anhand des Änderungsdatums, ob
    sie eine Datei neu einlesen.
    """
    getan: list[str] = []

    for kennung, aenderung in profil.dateien.items():
        ziel = _pfad_aufloesen(aenderung.pfad, spielordner, praefix)

        if not aenderung.werte:
            continue

        if ziel.exists():
            ordner = sicherungsordner(profil.steam_app_id, profil.name)
            ordner.mkdir(parents=True, exist_ok=True)
            sicherung = ordner / f"{ziel.name}.{time.strftime('%Y%m%d-%H%M%S')}"
            shutil.copy2(ziel, sicherung)
            alt = ziel.read_text(encoding="utf-8", errors="replace")
            # Erst ins Journal, dann ändern. Andersherum wäre ein Absturz
            # zwischen beiden Schritten nicht mehr aufzulösen.
            journal.vermerken("datei", str(ziel), str(sicherung))
        else:
            alt = ""
            # Kein Vorher heißt: beim Zurücksetzen wieder löschen.
            journal.vermerken("datei", str(ziel), None)

        if aenderung.zusammenfuehren:
            neu = godot_cfg.zusammenfuehren(alt, aenderung.werte)
        else:
            neu = godot_cfg.zusammenfuehren("", aenderung.werte)

        ziel.parent.mkdir(parents=True, exist_ok=True)
        ziel.write_text(neu, encoding="utf-8")
        getan.append(f"{kennung}: {ziel}")

    return getan


def zuruecksetzen(journal: Journal) -> list[str]:
    """Alles aus dem Journal rückgängig machen.

    In umgekehrter Reihenfolge, weil spätere Änderungen auf früheren
    aufbauen können. Und mit Fehlertoleranz: Wenn ein Eintrag sich nicht
    zurücksetzen lässt, werden die übrigen trotzdem abgearbeitet. Ein
    Aufräumer, der beim ersten Problem stehenbleibt, hinterlässt mehr
    Unordnung als einer, der weitermacht und berichtet.
    """
    bericht: list[str] = []

    for eintrag in reversed(journal.eintraege):
        if eintrag.stellschraube != "datei":
            bericht.append(f"unbekannte Stellschraube: {eintrag.stellschraube}")
            continue

        ziel = Path(eintrag.ziel)
        try:
            if eintrag.vorher is None:
                ziel.unlink(missing_ok=True)
                bericht.append(f"{ziel} wieder entfernt")
            else:
                sicherung = Path(eintrag.vorher)
                if not sicherung.exists():
                    bericht.append(f"FEHLT: Sicherung {sicherung} für {ziel}")
                    continue
                shutil.copy2(sicherung, ziel)
                bericht.append(f"{ziel} aus Sicherung wiederhergestellt")
        except OSError as fehler:
            bericht.append(f"FEHLER bei {ziel}: {fehler}")

    return bericht
