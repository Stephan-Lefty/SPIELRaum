"""Godots ``override.cfg`` ändern, ohne kaputtzumachen, was drinsteht.

Diese Datei gibt es wegen eines konkreten Falls. Road to Vostok liegt mit
einer ``override.cfg`` auf der Platte, die so anfängt::

    [autoload_prepend]
    ModLoader="*res://modloader.gd"

Das ist die Anmeldung des Mod-Loaders. Wer diese Datei zum Setzen einer
Grafikeinstellung einfach überschreibt, schaltet damit sechzehn Mods ab – und
merkt es erst, wenn das Spiel läuft und alles fehlt.

Der Mod-Loader-Installer macht es richtig und schreibt es auch hin: *»merges
into user's existing override.cfg (forces template key values, preserves user
sections/keys)«*. Genau dieses Verhalten bildet dieses Modul nach.

**Der Ansatz ist bewusst zeilenweise, nicht über ``configparser``.** Godots
Format sieht INI ähnlich, ist aber keines: Werte sind GDScript-Literale, und
``configparser`` schreibt beim Zurückschreiben alles neu – Reihenfolge,
Anführungszeichen und Kommentare gehen dabei verloren. Bei einer Datei, die
jemand anders verwaltet, ist das inakzeptabel. Hier wird deshalb nur das
angefasst, was angefasst werden soll; jede andere Zeile geht unverändert
durch, Zeichen für Zeichen.
"""

from __future__ import annotations

import re

ABSCHNITT = re.compile(r"^\s*\[([^\]]+)\]\s*$")
ZUWEISUNG = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_/]*)\s*=")


def lesen(text: str) -> dict[str, dict[str, str]]:
    """Die Datei in Abschnitte und Schlüssel zerlegen – nur zum Nachsehen."""
    ergebnis: dict[str, dict[str, str]] = {}
    aktuell = ""
    for zeile in text.splitlines():
        if treffer := ABSCHNITT.match(zeile):
            aktuell = treffer.group(1)
            ergebnis.setdefault(aktuell, {})
        elif treffer := ZUWEISUNG.match(zeile):
            schluessel = treffer.group(1)
            _, _, wert = zeile.partition("=")
            ergebnis.setdefault(aktuell, {})[schluessel] = wert.strip()
    return ergebnis


def zusammenfuehren(text: str, werte: dict[str, dict[str, str]]) -> str:
    """Werte setzen und alles andere unangetastet lassen.

    Drei Fälle, und alle drei kommen vor:

    * Der Schlüssel steht schon im richtigen Abschnitt → die Zeile wird
      ersetzt, alle anderen bleiben.
    * Der Abschnitt gibt es, der Schlüssel nicht → die Zeile wird ans Ende
      des Abschnitts gehängt, vor den nächsten ``[...]``.
    * Den Abschnitt gibt es nicht → er wird hinten angefügt.
    """
    if not werte:
        return text

    zeilen = text.splitlines()
    offen = {a: dict(s) for a, s in werte.items()}  # was noch zu setzen ist
    ausgabe: list[str] = []
    aktuell = ""

    def abschnitt_abschliessen() -> None:
        """Noch nicht gesetzte Schlüssel dieses Abschnitts nachtragen."""
        for schluessel, wert in offen.get(aktuell, {}).items():
            ausgabe.append(f"{schluessel}={wert}")
        offen.pop(aktuell, None)

    for zeile in zeilen:
        if treffer := ABSCHNITT.match(zeile):
            # Bevor der neue Abschnitt beginnt: den alten vervollständigen.
            # Leerzeilen am Ende des Abschnitts dabei hinter die neuen Werte
            # schieben, damit die Datei lesbar bleibt.
            nachlauf: list[str] = []
            while ausgabe and not ausgabe[-1].strip():
                nachlauf.append(ausgabe.pop())
            abschnitt_abschliessen()
            ausgabe.extend(nachlauf)

            aktuell = treffer.group(1)
            ausgabe.append(zeile)
            continue

        if (treffer := ZUWEISUNG.match(zeile)) and aktuell in offen:
            schluessel = treffer.group(1)
            if schluessel in offen[aktuell]:
                ausgabe.append(f"{schluessel}={offen[aktuell].pop(schluessel)}")
                continue

        ausgabe.append(zeile)

    abschnitt_abschliessen()

    # Was übrig ist, sind Abschnitte, die es in der Datei nicht gab.
    for abschnitt, schluessel in offen.items():
        if not schluessel:
            continue
        if ausgabe and ausgabe[-1].strip():
            ausgabe.append("")
        ausgabe.append(f"[{abschnitt}]")
        ausgabe.extend(f"{s}={w}" for s, w in schluessel.items())

    ergebnis = "\n".join(ausgabe)
    # Godot schreibt seine Dateien mit abschließendem Zeilenumbruch. Ohne ihn
    # hängt beim nächsten Anhängen alles in einer Zeile.
    return ergebnis if ergebnis.endswith("\n") else ergebnis + "\n"
