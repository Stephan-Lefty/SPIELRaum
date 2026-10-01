"""Prüft den Leser für Godot-Ressourcen.

Der wichtigste Test ist ``test_tastenbelegung_bleibt_unberuehrt``. Bei Road
to Vostok stehen die Tastenbelegungen in ``[sub_resource]``-Blöcken derselben
Datei wie die Grafikeinstellungen. Ein Schreibfehler dort, und der Anwender
steht in einem Spiel, in dem die Maus nicht mehr tut, was sie soll – wegen
einer Grafikeinstellung, die er ändern wollte.

Das Beispiel ist eine gekürzte Abschrift der echten Datei vom 01.10.2026.
"""

import pytest

from spielraum import godot_tres

ECHT = '''[gd_resource type="Resource" script_class="Preferences" load_steps=3 format=3]

[ext_resource type="Script" path="res://Scripts/Preferences.gd" id="1"]

[sub_resource type="InputEventKey" id="InputEventKey_7g6mt"]
pressed = true
keycode = 4194322
physical_keycode = 4194322
key_label = 4194322

[sub_resource type="InputEventKey" id="InputEventKey_wpugq"]
pressed = true
keycode = 4194325
location = 2

[resource]
script = ExtResource("1")
aimSensitivity = 1.0
contrast = 1.05
map = true
detailShadows = 2
reflections = 2
ambientOcclusion = 1
frameLimit = 5
rendering = 1
sharpness = 1.0
lighting = 1
antialiasing = 1
smaa = 1
'''


def test_nur_der_resource_abschnitt_wird_gelesen():
    """»keycode« steht in einem sub_resource und darf nicht auftauchen."""
    werte = godot_tres.lesen(ECHT)
    assert werte["lighting"] == "1"
    assert werte["detailShadows"] == "2"
    assert "keycode" not in werte
    assert "physical_keycode" not in werte
    assert "location" not in werte


def test_tastenbelegung_bleibt_unberuehrt():
    """Der Fall, für den dieses Modul vorsichtig ist.

    Die sub_resource-Blöcke enthalten bei Road to Vostok die
    Tastenbelegungen. Sie müssen eine Änderung Zeichen für Zeichen
    überstehen.
    """
    neu = godot_tres.schreiben(ECHT, {"lighting": 3, "antialiasing": 3})

    for zeile in ("keycode = 4194322", "physical_keycode = 4194322",
                  "location = 2", "pressed = true"):
        assert zeile in neu, f"{zeile} ist verlorengegangen"
    assert neu.count("[sub_resource") == 2
    assert "lighting = 3" in neu
    assert "antialiasing = 3" in neu


def test_gleichnamiger_schluessel_im_sub_resource():
    """Steht derselbe Name in beiden Abschnitten, darf nur der aus
    [resource] geändert werden."""
    text = (
        '[gd_resource type="Resource" format=3]\n\n'
        '[sub_resource type="InputEventKey" id="A"]\n'
        'lighting = 99\n\n'
        '[resource]\n'
        'lighting = 1\n'
    )
    neu = godot_tres.schreiben(text, {"lighting": 2})
    assert "lighting = 99" in neu   # der fremde bleibt
    assert "lighting = 2" in neu
    assert "lighting = 1" not in neu


def test_typen_bleiben_erhalten():
    """1.0 ist ein Gleitkommawert, 1 eine ganze Zahl - das soll so bleiben."""
    neu = godot_tres.schreiben(ECHT, {"sharpness": 2, "lighting": 2, "map": False})
    assert "sharpness = 2.0" in neu   # war 1.0, bleibt Gleitkomma
    assert "lighting = 2" in neu      # war 1, bleibt ganzzahlig
    assert "map = false" in neu       # war true, bleibt Wahrheitswert
    assert "map = False" not in neu   # GDScript kennt kein großes F


def test_unbekannter_schluessel_faellt_auf():
    """Ein Tippfehler soll sich melden, statt stillschweigend nichts zu tun."""
    with pytest.raises(godot_tres.TresFehler, match="lightning"):
        godot_tres.schreiben(ECHT, {"lightning": 2})


def test_unbekannter_schluessel_mit_streng_false():
    neu = godot_tres.schreiben(ECHT, {"gibtsnicht": 1}, streng=False)
    assert neu == ECHT  # nichts passiert, aber auch nichts kaputt


def test_ohne_werte_bleibt_alles_gleich():
    assert godot_tres.schreiben(ECHT, {}) == ECHT


def test_einrueckung_und_abstaende_bleiben():
    text = (
        '[gd_resource type="Resource" format=3]\n\n'
        '[resource]\n'
        '  lighting   =   1\n'
    )
    neu = godot_tres.schreiben(text, {"lighting": 2})
    assert "  lighting   =   2" in neu


def test_pruefen_erkennt_fremde_datei():
    with pytest.raises(godot_tres.TresFehler, match="keine Godot-Ressource"):
        godot_tres.pruefen("[autoload]\nModLoader=\"x\"\n")


def test_pruefen_erkennt_fehlenden_abschnitt():
    with pytest.raises(godot_tres.TresFehler, match="kein.*resource.*Abschnitt"):
        godot_tres.pruefen('[gd_resource type="Resource" format=3]\n\n'
                           '[sub_resource type="X" id="A"]\nwert = 1\n')


def test_pruefen_nimmt_die_echte_datei_an():
    godot_tres.pruefen(ECHT)  # darf nicht werfen


def test_rundlauf():
    """Schreiben und wieder lesen ergibt, was geschrieben wurde."""
    neu = godot_tres.schreiben(ECHT, {"lighting": 4, "detailShadows": 1})
    werte = godot_tres.lesen(neu)
    assert werte["lighting"] == "4"
    assert werte["detailShadows"] == "1"
    assert werte["reflections"] == "2"  # unberührt
