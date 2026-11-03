"""Zwischen den Richtungen umschalten – Optik, Ausgeglichen, Leistung.

Das ist der kleine Bruder der [Messfahrt](../docs/messfahrt.md): Statt drei
Läufe zu verwalten, setzt dieses Modul **eine** Variante und lässt sie
stehen. Damit lässt sich eine Messfahrt von Hand fahren, bevor die Automatik
steht – und die Automatik wird später genau diese Funktionen rufen.

**Der Unterschied zum Spielstart.** Was ``spielraum starten`` an einer Datei
ändert, wird beim Spielende zurückgenommen – dafür gibt es das Journal. Eine
Variante soll dagegen **bleiben**: Wer auf »Leistung« stellt, will nicht, dass
nach dem Spielen wieder »Optik« dasteht.

Trotzdem gibt es eine Sicherung, und zwar eine einzige je Spiel: den Zustand
vor der ersten Umstellung. Sie heißt ``vor-erster-variante`` und wird nie
überschrieben. Wer dreimal umschaltet und dann zurück will, landet dort, wo
er angefangen hat – nicht bei der vorletzten Variante.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from . import godot_cfg, godot_tres, stellschrauben
from .profil import Profil

SICHERUNG = "vor-erster-variante"


class VariantenFehler(Exception):
    pass


def _sicherungspfad(profil: Profil, kennung: str) -> Path:
    ordner = stellschrauben.sicherungsordner(profil.steam_app_id, profil.name)
    return ordner / f"{kennung}.{SICHERUNG}"


def anwenden(
    profil: Profil,
    name: str,
    spielordner: Path | None = None,
    praefix: Path | None = None,
) -> list[str]:
    """Eine Variante setzen. Gibt zurück, was geändert wurde."""
    variante = profil.varianten.get(name)
    if variante is None:
        raise VariantenFehler(
            f"»{name}« kennt dieses Profil nicht. Vorhanden: "
            + (", ".join(profil.varianten) or "keine")
        )

    bericht: list[str] = []
    for kennung, werte in variante.dateien.items():
        aenderung = profil.dateien[kennung]
        ziel = stellschrauben._pfad_aufloesen(aenderung.pfad, spielordner, praefix)
        if not ziel.exists():
            raise VariantenFehler(
                f"{ziel} gibt es nicht. Bei Grafikeinstellungen legt das Spiel "
                "die Datei beim ersten Start selbst an – einmal starten und "
                "beenden genügt."
            )

        alt = ziel.read_text(encoding="utf-8", errors="replace")

        # Die eine Sicherung je Spiel, angelegt vor der ersten Umstellung
        # und danach nie wieder angefasst.
        sicherung = _sicherungspfad(profil, kennung)
        if not sicherung.exists():
            sicherung.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ziel, sicherung)
            bericht.append(f"Ausgangszustand gesichert: {sicherung.name}")

        neu = stellschrauben._neuer_inhalt(aenderung, alt, werte)
        if neu == alt:
            bericht.append(f"{kennung}: stand schon so")
            continue
        stellschrauben.atomar_schreiben(ziel, neu)
        bericht.append(f"{kennung}: " + ", ".join(f"{k}={v}" for k, v in werte.items()))

    return bericht


def _unsere_schluessel(profil: Profil, kennung: str) -> dict:
    """Alle Schlüssel dieser Datei, die SPIELRaum überhaupt anfassen kann.

    Das ist die Vereinigung aus dem festen ``[dateien]``-Block und allen
    Varianten. Mehr als diese Schlüssel hat SPIELRaum nie geschrieben – also
    darf es auch nie mehr zurücksetzen.

    Die Werte sind hier gleichgültig, nur die Namen zählen; die alten Werte
    kommen aus der Sicherung.
    """
    aenderung = profil.dateien[kennung]
    gesammelt: dict = {}

    def aufnehmen(werte: dict) -> None:
        for schluessel, wert in werte.items():
            if isinstance(wert, dict):
                gesammelt.setdefault(schluessel, {}).update(dict.fromkeys(wert))
            else:
                gesammelt[schluessel] = None

    aufnehmen(aenderung.werte)
    for variante in profil.varianten.values():
        aufnehmen(variante.dateien.get(kennung, {}))
    return gesammelt


def zuruecksetzen(
    profil: Profil,
    spielordner: Path | None = None,
    praefix: Path | None = None,
) -> list[str]:
    """Die von SPIELRaum gesetzten Werte auf den Ausgangszustand zurückholen.

    Hier stand bis zum 03.11.2026 ein ``shutil.copy2`` der ganzen Sicherung
    über die Zieldatei – derselbe Fehler wie im Journalweg, nur mit einer
    älteren Sicherung: Die hier liegt vom Tag der *ersten* Umstellung. Bei
    Road to Vostok war sie fünf Wochen alt, und jedes Zurücksetzen hätte das
    Spiel auf den Stand vom 01.10.2026 zurückgeworfen – samt Tastenbelegung,
    Lautstärken und Blickfeld.

    Jetzt werden nur die Schlüssel zurückgeschrieben, die über Profil oder
    Varianten überhaupt in unserer Hand liegen. Die alten Werte stehen in
    der Sicherung, die aktuelle Datei liefert alles andere.
    """
    bericht: list[str] = []
    for kennung, aenderung in profil.dateien.items():
        sicherung = _sicherungspfad(profil, kennung)
        if not sicherung.exists():
            continue
        ziel = stellschrauben._pfad_aufloesen(aenderung.pfad, spielordner, praefix)

        unsere = _unsere_schluessel(profil, kennung)
        alt_text = sicherung.read_text(encoding="utf-8", errors="replace")
        alt, fehlende = stellschrauben.alte_werte(aenderung, alt_text, unsere)

        if not ziel.exists():
            shutil.copy2(sicherung, ziel)
            bericht.append(f"{kennung}: war weg – ganz aus {sicherung.name} geholt")
            continue
        if not alt:
            bericht.append(
                f"{kennung}: in {sicherung.name} steht keiner unserer Schlüssel – "
                "nichts zurückzusetzen")
            continue

        jetzt = ziel.read_text(encoding="utf-8", errors="replace")
        neu = stellschrauben._werte_einsetzen(aenderung.art, jetzt, alt, fehlende)
        namen = stellschrauben._flach(alt)
        if neu == jetzt:
            bericht.append(f"{kennung}: stand schon auf dem Ausgangswert")
            continue
        stellschrauben.atomar_schreiben(ziel, neu)
        bericht.append(f"{kennung}: {', '.join(namen)} auf den Ausgangswert zurück")

    if not bericht:
        bericht.append("Nichts zurückzusetzen – es wurde nie eine Variante gesetzt.")
    return bericht


def aktuelle(
    profil: Profil,
    spielordner: Path | None = None,
    praefix: Path | None = None,
) -> str | None:
    """Welche Variante steht gerade in den Dateien?

    ``None``, wenn die Werte zu keiner passen – etwa weil jemand im
    Spielmenü etwas anderes eingestellt hat. Das ist kein Fehler, sondern
    eine Auskunft, und für die Messfahrt die entscheidende: Ein Lauf zählt
    nur, wenn am Ende noch dieselbe Variante dasteht wie am Anfang.
    """
    for name, variante in profil.varianten.items():
        passt = True
        for kennung, werte in variante.dateien.items():
            aenderung = profil.dateien[kennung]
            try:
                ziel = stellschrauben._pfad_aufloesen(aenderung.pfad, spielordner, praefix)
                inhalt = ziel.read_text(encoding="utf-8", errors="replace")
            except (OSError, FileNotFoundError):
                return None
            vorhanden = (godot_tres.lesen(inhalt) if aenderung.art == "godot-tres"
                         else godot_cfg.lesen(inhalt))
            for schluessel, wert in werte.items():
                if str(vorhanden.get(schluessel, "")).strip() != str(wert).strip():
                    passt = False
                    break
            if not passt:
                break
        if passt:
            return name
    return None
