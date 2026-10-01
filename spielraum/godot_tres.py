"""Godot-Ressourcen (``.tres``) lesen und einzelne Werte ändern.

Hier liegen die Grafikeinstellungen vieler Godot-Spiele. Bei Road to Vostok
ist es ``Preferences.tres`` im Proton-Präfix, und darin steckte am
01.10.2026 der einzige Hebel, der an diesem Spiel wirklich etwas bewegte:
Beleuchtung und Kantenglättung zurückgenommen brachten 48 % mehr Bilder –
mehr als alle Systemstellschrauben zusammen.

## Der Aufbau

Eine ``.tres`` ist Text mit mehreren Abschnitten::

    [gd_resource type="Resource" script_class="Preferences" format=3]

    [ext_resource type="Script" path="res://Scripts/Preferences.gd" id="1"]

    [sub_resource type="InputEventKey" id="InputEventKey_7g6mt"]
    pressed = true
    keycode = 4194322

    [resource]
    script = ExtResource("1")
    detailShadows = 2
    lighting = 3

**Angefasst wird ausschließlich ``[resource]``.** Das ist keine Bequemlichkeit,
sondern die Sicherheitszusage dieses Moduls: In den ``[sub_resource]``-Blöcken
stehen bei Road to Vostok die **Tastenbelegungen**. Ein Schreibfehler dort,
und der Anwender steht in einem Spiel, in dem die Maus nicht mehr tut, was
sie soll – wegen einer Grafikeinstellung, die er ändern wollte.

## Warum wieder zeilenweise

Wie bei ``godot_cfg``: Es wird nur die eine Zeile ersetzt, die geändert
werden soll. Jede andere geht unverändert durch, Zeichen für Zeichen –
einschließlich Reihenfolge, Leerzeilen und allem, was das Spiel sonst noch
hineinschreibt. Eine Datei, die ein fremdes Programm verwaltet, baut man
nicht neu auf.

## Typen bleiben Typen

``1.0`` ist in GDScript ein Gleitkommawert, ``1`` eine ganze Zahl, ``true``
ein Wahrheitswert. Wer aus ``sharpness = 1.0`` ein ``sharpness = 1`` macht,
ändert den Typ – und Godot kann beim Einlesen anders reagieren, als das
Spiel erwartet. ``schreiben`` behält deshalb die Schreibweise des alten
Wertes bei.
"""

from __future__ import annotations

import re

ABSCHNITT = re.compile(r"^\s*\[([a-z_]+)[\s\]]")
ZUWEISUNG = re.compile(r"^(\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*=\s*)(.*)$")

# Der Abschnitt mit den Einstellungen. Alles andere ist tabu.
EIGENER_ABSCHNITT = "resource"


class TresFehler(Exception):
    """Die Datei sieht nicht aus wie eine Godot-Ressource."""


def lesen(text: str) -> dict[str, str]:
    """Die Werte aus ``[resource]`` – als Text, unverändert wie sie dastehen.

    Bewusst keine Umwandlung in Zahlen: Wer ``2`` liest und ``2`` zurück-
    schreibt, soll dieselben zwei Zeichen zurückbekommen. Die Deutung der
    Werte ist Sache des Aufrufers.
    """
    werte: dict[str, str] = {}
    drin = False
    for zeile in text.splitlines():
        if treffer := ABSCHNITT.match(zeile):
            drin = treffer.group(1) == EIGENER_ABSCHNITT
            continue
        if drin and (treffer := ZUWEISUNG.match(zeile)):
            werte[treffer.group(2)] = treffer.group(4).strip()
    return werte


def _angleichen(alt: str, neu: object) -> str:
    """Den neuen Wert so schreiben, wie der alte geschrieben war.

    Stand dort ``1.0`` und es kommt eine ``2``, wird daraus ``2.0``. Stand
    dort ``true``, wird aus einem Wahrheitswert ``false`` – nicht ``False``,
    das kennt GDScript nicht.
    """
    if isinstance(neu, bool):
        return "true" if neu else "false"

    alt = alt.strip()
    if alt in ("true", "false"):
        return "true" if neu else "false"

    # Gleitkomma erkennt man am Punkt oder am Exponenten.
    if isinstance(neu, (int, float)) and ("." in alt or "e" in alt.lower()):
        return f"{float(neu)}"
    if isinstance(neu, float) and neu.is_integer() and "." not in alt:
        return str(int(neu))
    return str(neu)


def schreiben(text: str, werte: dict[str, object], streng: bool = True) -> str:
    """Werte in ``[resource]`` ändern und alles andere unangetastet lassen.

    ``streng`` bestimmt, was mit unbekannten Namen geschieht. Voreingestellt
    ist ein Fehler: Wer ``lightning`` statt ``lighting`` schreibt, soll das
    erfahren, statt sich zu wundern, warum nichts passiert. Neue Schlüssel
    anzulegen wäre hier auch falsch – das Spiel kennt sie nicht, und die
    Datei gehört ihm.
    """
    if not werte:
        return text

    vorhanden = lesen(text)
    if streng:
        unbekannt = sorted(set(werte) - set(vorhanden))
        if unbekannt:
            raise TresFehler(
                "Diese Einstellungen gibt es in der Datei nicht: "
                + ", ".join(unbekannt)
                + ". Vorhanden sind: "
                + ", ".join(sorted(vorhanden))
            )

    offen = dict(werte)
    ausgabe: list[str] = []
    drin = False

    for zeile in text.splitlines():
        if treffer := ABSCHNITT.match(zeile):
            drin = treffer.group(1) == EIGENER_ABSCHNITT
            ausgabe.append(zeile)
            continue

        if drin and (treffer := ZUWEISUNG.match(zeile)):
            name = treffer.group(2)
            if name in offen:
                einrueckung, _, gleich, alt = treffer.groups()
                neu = _angleichen(alt, offen.pop(name))
                ausgabe.append(f"{einrueckung}{name}{gleich}{neu}")
                continue

        ausgabe.append(zeile)

    ergebnis = "\n".join(ausgabe)
    # Godot schreibt mit abschließendem Zeilenumbruch.
    if text.endswith("\n") and not ergebnis.endswith("\n"):
        ergebnis += "\n"
    return ergebnis


def pruefen(text: str) -> None:
    """Sieht die Datei überhaupt wie eine Godot-Ressource aus?

    Ein Spiel, das sein Format wechselt, oder ein verwechselter Pfad sollen
    auffallen, **bevor** geschrieben wird – nicht danach.
    """
    if not text.lstrip().startswith("[gd_resource"):
        raise TresFehler(
            "Das ist keine Godot-Ressource – die Datei fängt nicht mit "
            "[gd_resource an."
        )
    if not any(ABSCHNITT.match(z) and ABSCHNITT.match(z).group(1) == EIGENER_ABSCHNITT
               for z in text.splitlines()):
        raise TresFehler("In der Datei gibt es keinen [resource]-Abschnitt.")
