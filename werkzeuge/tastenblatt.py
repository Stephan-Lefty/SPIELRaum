#!/usr/bin/env python3
"""Erzeugt ein Tastenblatt zum Danebenlegen -- aus Profil und Spieldatei.

Warum das ein Werkzeug ist und kein Skript nebenher: Am 23.10.2026
entstanden zwei solche Übersichten aus Wegwerfskripten in /tmp. Fünf
Minuten später waren sie falsch, weil die Belegung sich geändert hatte, und
am selben Abend waren die Skripte weg. Was aus den echten Quellen erzeugt
wird, kann nicht veralten.

**Die wichtigste Eigenschaft:** Hier steht die Taste, die *gedrückt* wird --
nicht die, die im Spielmenü steht. Seit keyd dazwischensitzt, sind das zwei
verschiedene Dinge. Eine Übersicht, die »Space« schreibt, während man Bild
hoch drückt, ist schlimmer als keine.

Aufruf::

    python3 werkzeuge/tastenblatt.py 1963610 [ziel.md]

Die Ausgabe ist Markdown. Für ein PDF: durch einen beliebigen Wandler
schicken, etwa ``pandoc`` oder einen eigenen.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from spielraum import profil, steam  # noqa: E402

# --- Tastennamen -----------------------------------------------------------
# Links, wie keyd und die Spiele sie nennen. Rechts, wie sie beschriftet
# sind. »pageup« steht auf keiner deutschen Tastatur.
BESCHRIFTET = {
    "up": "Pfeil hoch", "down": "Pfeil runter",
    "left": "Pfeil links", "right": "Pfeil rechts",
    "pageup": "Bild hoch", "pagedown": "Bild runter",
    "home": "Pos 1", "end": "Ende", "insert": "Einfg", "delete": "Entf",
    "space": "Leertaste", "enter": "Enter", "esc": "Esc", "tab": "Tab",
    "leftshift": "Umschalt links", "rightshift": "Umschalt rechts",
    "leftcontrol": "Strg links", "rightcontrol": "Strg rechts",
    "leftalt": "Alt links", "rightalt": "Alt Gr",
    "layer(shift)": "Umschalt", "layer(control)": "Strg",
    "layer(alt)": "Alt", "layer(meta)": "Meta",
}

# --- Godot ----------------------------------------------------------------
# Road to Vostok speichert Tastencodes, keine Namen. Belegt am 23.10.2026
# über die Angabe des Anwenders: forward lag auf 4194320, und das ist
# Pfeil hoch.
SPECIAL = 1 << 22
GODOT_SONDER = {
    1: "Esc", 2: "Tab", 4: "Rücktaste", 5: "Enter", 6: "Enter (Ziffernblock)",
    7: "Einfg", 8: "Entf", 13: "Pos 1", 14: "Ende",
    15: "Pfeil links", 16: "Pfeil hoch", 17: "Pfeil rechts", 18: "Pfeil runter",
    19: "Bild hoch", 20: "Bild runter",
    21: "Umschalt", 22: "Strg", 23: "Meta", 24: "Alt",
}
for _i in range(1, 13):
    GODOT_SONDER[27 + _i] = f"F{_i}"

GODOT_SEITE = {"1": " links", "2": " rechts"}

# Maustasten in Fingern statt Seiten: Wer die Maustasten vertauscht hat,
# findet »linke Maustaste« unter dem Mittelfinger.
GODOT_MAUS = {
    1: "Zeigefinger", 2: "Mittelfinger", 3: "Radklick",
    4: "Rad hoch", 5: "Rad runter", 6: "Rad links", 7: "Rad rechts",
    8: "Daumen hinten", 9: "Daumen vorn",
}

SPIEL_DEUTSCH = {
    1203620: {  # Enshrouded
        "MovementUp": "Vorwärts", "MovementDown": "Rückwärts",
        "MovementLeft": "Seitwärts links", "MovementRight": "Seitwärts rechts",
        "CameraLeft": "Kamera links", "CameraRight": "Kamera rechts",
        "CameraUp": "Kamera hoch", "CameraDown": "Kamera runter",
        "CameraZoomIn": "Kamera heran", "CameraZoomOut": "Kamera weg",
        "Jump": "Springen", "Glider": "Gleiter", "Sprint": "Sprinten",
        "Walk": "Gehen", "Sneak": "Schleichen", "Evade": "Ausweichen",
        "MainhandAction": "Angriff", "ContextualAction": "Benutzen / Aufheben",
        "Block": "Blocken", "CancelAction": "Abbrechen",
        "SpecialAbility": "Spezialfähigkeit", "DropItem": "Ablegen",
        "LootTakeAll": "Alles nehmen", "RangedCombatArm": "Fernkampf anlegen",
        "RangedCombatShoot": "Fernkampf schießen",
        "AmmunitionSelectPrevious": "Munition zurück",
        "AmmunitionSelectNext": "Munition vor",
        "LockCombatTarget": "Ziel festhalten",
        "ActionbarPreviousSlot": "Leiste zurück", "ActionbarNextSlot": "Leiste vor",
        "ActionbarSwapPage": "Leiste umblättern",
        "ShowEmoteWheel": "Gestenrad", "ShowActionbarWheel": "Aktionsrad",
        "HeadDive": "Kopfsprung", "SwimStartDiving": "Tauchen",
        "DiveAscend": "Auftauchen", "DiveDescend": "Abtauchen",
        "UiBackpack": "Rucksack", "UiMap": "Karte", "UiCrafting": "Handwerk",
        "UiBuildingMenu": "Baumenü", "UiInGameMenu": "Spielmenü",
        "UiCharacter": "Charakter", "UiJournal": "Tagebuch",
        "UiSkills": "Fähigkeiten", "UiSocial": "Gruppe",
        "UiSystemMenu": "Systemmenü", "UiTextChat": "Textchat",
        "VoiceChatPushToTalk": "Sprechtaste",
        **{f"QuickUse{i}": f"Schnellzugriff {i + 1}" for i in range(10)},
    },
}

VOSTOK_DEUTSCH = {
    "aim": "Zielen", "ammo_check": "Munition prüfen", "backward": "Rückwärts",
    "canted": "Schrägvisier", "crouch": "Ducken", "decor": "Dekoration",
    "fire": "Schießen", "firemode": "Feuermodus", "flashlight": "Taschenlampe",
    "forward": "Vorwärts", "grenade_1": "Granate 1", "grenade_2": "Granate 2",
    "insert": "Einsetzen", "inspect": "Betrachten", "interact": "Benutzen",
    "interface": "Inventar", "item_drop": "Ablegen", "item_equip": "Ausrüsten",
    "item_rotate": "Drehen", "item_transfer": "Übergeben", "jump": "Springen",
    "knife": "Messer", "laser": "Laser", "lean_L": "Neigen links",
    "lean_R": "Neigen rechts", "left": "Seitwärts links", "nvg": "Nachtsicht",
    "place": "Platzieren", "prepare": "Vorbereiten", "primary": "Primärwaffe",
    "rail_movement": "Schiene verschieben", "reload": "Nachladen",
    "right": "Seitwärts rechts", "secondary": "Sekundärwaffe",
    "secondary_optic": "Zweitvisier", "sprint": "Sprinten",
    "weapon_high": "Waffe hoch", "weapon_low": "Waffe runter",
}


def beschriftet(name: str) -> str:
    if name in BESCHRIFTET:
        return BESCHRIFTET[name]
    return name.upper() if len(name) == 1 else name


def godot_taste(code: int, seite: str | None = None) -> str:
    """Einen Godot-Tastencode in die Aufschrift der Taste übersetzen."""
    if code == 0x7FFFFF:
        return "— kein gültiger Eintrag —"
    if code & SPECIAL:
        name = GODOT_SONDER.get(code - SPECIAL, f"Sondertaste {code - SPECIAL}")
        return name + GODOT_SEITE.get(seite or "", "")
    if code == 32:
        return "Leertaste"
    if 32 < code < 127:
        return chr(code).upper()
    return f"Code {code}"


def vostok_lesen(pfad: Path) -> list[tuple[str, str, str]]:
    """Die Belegung aus ``Preferences.tres`` holen.

    Nur der ``[resource]``-Teil zählt für die Zuordnung; die Tastencodes
    stehen in den ``[sub_resource]``-Blöcken darüber.
    """
    t = pfad.read_text(errors="replace")
    subs: dict[str, tuple[str, str]] = {}
    for block in re.split(r"\n(?=\[sub_resource)", t):
        kopf = re.match(r'\[sub_resource type="(\w+)" id="([^"]+)"\]', block)
        if not kopf:
            continue
        art, sid = kopf.groups()
        if art == "InputEventKey":
            code = re.search(r"physical_keycode = (\d+)", block) or \
                   re.search(r"keycode = (\d+)", block)
            seite = re.search(r"location = (\d+)", block)
            subs[sid] = ("Tastatur", godot_taste(int(code.group(1)),
                                                 seite.group(1) if seite else None)
                         ) if code else ("Tastatur", "— nicht belegt —")
        elif art == "InputEventMouseButton":
            knopf = re.search(r"button_index = (\d+)", block)
            nummer = int(knopf.group(1)) if knopf else 1
            subs[sid] = ("Maus", GODOT_MAUS.get(nummer, f"Maustaste {nummer}"))
        else:
            subs[sid] = ("Gamepad", "Gamepad")

    zeilen = []
    for m in re.finditer(r'"(\w+)": SubResource\("([^"]+)"\)', t):
        aktion, sid = m.groups()
        geraet, taste = subs.get(sid, ("?", "?"))
        zeilen.append((VOSTOK_DEUTSCH.get(aktion, aktion), geraet, taste))
    return zeilen


# --- Steams Cloud-Ordner ---------------------------------------------------
# Manche Spiele legen ihre Einstellungen nicht ins Proton-Präfix, sondern in
# Steams Cloud-Ordner. Die Benutzerkennung darin steht nirgends fest --
# gesucht wird deshalb, statt sie zu erraten.
ENSHROUDED_MAUS = {
    "Left": "Zeigefinger", "Right": "Mittelfinger", "Middle": "Radklick",
    "Button4": "Daumen hinten", "Button5": "Daumen vorn",
}


def cloud_datei(app_id: int, name: str) -> Path | None:
    """Eine Datei aus Steams Cloud-Ordner dieses Spiels suchen."""
    for wurzel in (Path.home() / ".local/share/Steam/userdata",
                   Path.home() / ".steam/steam/userdata"):
        if not wurzel.is_dir():
            continue
        for benutzer in wurzel.iterdir():
            kandidat = benutzer / str(app_id) / "remote" / name
            if kandidat.exists():
                return kandidat
    return None


def json_belegung(pfad: Path, uebersetzung: dict[str, str]) -> list[tuple[str, str, str]]:
    """Die Belegung aus einer JSON-Datei im Enshrouded-Format lesen.

    Der Aufbau ist ``input.keyboardMouse.bindings.{gameplay,ui}``, jeweils
    eine Liste aus ``{id, action:{primary,secondary}}``.
    """
    import json

    d = json.loads(pfad.read_text(encoding="utf-8", errors="replace"))
    try:
        bind = d["input"]["keyboardMouse"]["bindings"]
    except (KeyError, TypeError):
        return []

    def eine(op) -> tuple[str, str] | None:
        o = op["operation"]
        vor = "+".join(x["id"] for x in op.get("modifiers", []))
        vor = f"{vor} + " if vor else ""
        if o["type"] == "Key":
            return "Tastatur", vor + beschriftet(o["id"].lower())
        if o["type"] == "MouseButton":
            return "Maus", vor + ENSHROUDED_MAUS.get(o["id"], o["id"])
        if o["type"] == "MouseWheel":
            return "Maus", vor + ("Rad hoch" if o["axis"] == "PositiveY" else "Rad runter")
        if o["type"] == "MouseMove":
            return "Maus", "Maus bewegen"
        return None

    zeilen = []
    for bereich in ("gameplay", "ui"):
        for eintrag in bind.get(bereich, []):
            if eintrag["id"] == "Count":  # kein Befehl, nur der Zähler am Ende
                continue
            gefunden = [eine(eintrag["action"][s]) for s in ("primary", "secondary")]
            gefunden = [g for g in gefunden if g]
            if not gefunden:
                continue
            geraet = "Maus" if any(g[0] == "Maus" for g in gefunden) else "Tastatur"
            taste = " oder ".join(dict.fromkeys(g[1] for g in gefunden))
            zeilen.append((uebersetzung.get(eintrag["id"], eintrag["id"]), geraet, taste))
    return zeilen


def tabelle(zeilen, spalten) -> str:
    aus = ["| " + " | ".join(spalten) + " |",
           "|" + "|".join("---" for _ in spalten) + "|"]
    aus += ["| " + " | ".join(z) + " |" for z in zeilen]
    return "\n".join(aus)


def blatt(app_id: int) -> str:
    p = profil.finden(steam_app_id=app_id)
    if p is None:
        raise SystemExit(f"Für App {app_id} gibt es kein Profil.")

    spiel = next((s for s in steam.spiele_finden() if s.app_id == app_id), None)

    # Was keyd übersetzt -- rückwärts, damit die gedrückte Taste gefunden wird.
    zurueck = {ziel: beschriftet(taste) for taste, ziel in p.tasten.items()}

    teile = [f"# {p.name} — Tasten und Maus", "",
             "Maus links, Tastatur rechts. Hier steht die Taste, die du "
             "**drückst** — im Spielmenü steht etwas anderes, weil `keyd` "
             "dazwischen übersetzt.", ""]

    if p.tasten:
        teile += ["## Was keyd übersetzt", "",
                  tabelle([(beschriftet(t), beschriftet(z)) for t, z in p.tasten.items()],
                          ["du drückst", "das Spiel sieht"]), "",
                  "Die ursprüngliche Taste funktioniert weiter — `keyd` legt nur "
                  "eine zweite darauf. Sie liegt nur links und damit außer "
                  "Reichweite.", ""]

    # Die Spielbelegung. Godot legt sie ins Proton-Präfix, andere Spiele in
    # Steams Cloud-Ordner -- beide Wege werden versucht.
    zeilen: list[tuple[str, str, str]] = []
    if spiel and p.engine == "godot" and spiel.proton_praefix:
        tres = (spiel.proton_praefix / "pfx/drive_c/users/steamuser/AppData/Roaming"
                / p.name / "Preferences.tres")
        if tres.exists():
            zeilen = vostok_lesen(tres)
    if not zeilen:
        cloud = cloud_datei(app_id, "user_settings.json")
        if cloud is not None:
            zeilen = json_belegung(cloud, SPIEL_DEUTSCH.get(app_id, {}))

    if zeilen:
        maus = [(a, t) for a, g, t in zeilen if g == "Maus"]
        # Wo keyd übersetzt, die gedrückte Taste zeigen statt der, die das
        # Spiel sieht. Ohne das stünde »Space« da, während man Bild hoch drückt.
        tast = [(a, zurueck.get(t.lower(), zurueck.get(t, t)))
                for a, g, t in zeilen if g == "Tastatur"]
        teile += ["## Maus", "", tabelle(maus, ["Aktion", "liegt auf"]), "",
                  "## Tastatur", "",
                  "Wo keyd übersetzt, steht die gedrückte Taste.", "",
                  tabelle(sorted(tast), ["Aktion", "Taste"]), ""]

    teile += ["## Falls etwas klemmt", "",
              "Tastatur spinnt: `sudo systemctl stop keyd` — danach gilt wieder "
              "die Beschriftung auf den Tasten.", ""]
    return "\n".join(teile)


def main() -> int:
    if len(sys.argv) < 2 or not sys.argv[1].isdigit():
        print(__doc__)
        return 2
    text = blatt(int(sys.argv[1]))
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(text, encoding="utf-8")
        print(f"geschrieben: {sys.argv[2]}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
