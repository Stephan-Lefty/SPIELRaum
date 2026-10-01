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
        ziel.write_text(neu, encoding="utf-8")
        bericht.append(f"{kennung}: " + ", ".join(f"{k}={v}" for k, v in werte.items()))

    return bericht


def zuruecksetzen(
    profil: Profil,
    spielordner: Path | None = None,
    praefix: Path | None = None,
) -> list[str]:
    """Den Zustand vor der ersten Umstellung wiederherstellen."""
    bericht: list[str] = []
    for kennung, aenderung in profil.dateien.items():
        sicherung = _sicherungspfad(profil, kennung)
        if not sicherung.exists():
            continue
        ziel = stellschrauben._pfad_aufloesen(aenderung.pfad, spielordner, praefix)
        shutil.copy2(sicherung, ziel)
        bericht.append(f"{kennung}: aus {sicherung.name} wiederhergestellt")
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
