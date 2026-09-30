"""Prüft, dass das Zusammenführen nichts wegwirft.

Der wichtigste Test ist ``test_modloader_ueberlebt``. Er steht hier, weil der
Schaden im echten Fall unsichtbar wäre: Das Spiel startet, es stürzt nicht ab,
es fehlen nur alle Mods – und niemand verbindet das mit einem Programm, das
angeblich nur die Bildrate verbessern sollte.
"""

from spielraum import godot_cfg

# Genau der Inhalt, der am 30.09.2026 im Spielordner von Road to Vostok lag.
VOSTOK = """[autoload_prepend]
ModLoader="*res://modloader.gd"

[autoload]

"""


def test_modloader_ueberlebt():
    """Eine fremde Einstellung setzen darf den Mod-Loader nicht anrühren."""
    ergebnis = godot_cfg.zusammenfuehren(
        VOSTOK, {"rendering/renderer": {"rendering_method": '"mobile"'}}
    )
    assert 'ModLoader="*res://modloader.gd"' in ergebnis
    assert "[autoload_prepend]" in ergebnis
    assert "[autoload]" in ergebnis
    assert 'rendering_method="mobile"' in ergebnis


def test_vorhandenen_wert_ersetzen():
    text = '[rendering]\nmethod="forward_plus"\nandere=1\n'
    ergebnis = godot_cfg.zusammenfuehren(text, {"rendering": {"method": '"mobile"'}})
    assert 'method="mobile"' in ergebnis
    assert 'method="forward_plus"' not in ergebnis
    assert "andere=1" in ergebnis


def test_schluessel_in_vorhandenen_abschnitt():
    text = "[autoload]\nA=1\n\n[weiteres]\nB=2\n"
    ergebnis = godot_cfg.zusammenfuehren(text, {"autoload": {"C": "3"}})
    gelesen = godot_cfg.lesen(ergebnis)
    assert gelesen["autoload"] == {"A": "1", "C": "3"}
    assert gelesen["weiteres"] == {"B": "2"}


def test_neuer_abschnitt_wird_angehaengt():
    ergebnis = godot_cfg.zusammenfuehren(VOSTOK, {"display": {"vsync": "0"}})
    gelesen = godot_cfg.lesen(ergebnis)
    assert gelesen["display"] == {"vsync": "0"}
    assert gelesen["autoload_prepend"]["ModLoader"] == '"*res://modloader.gd"'


def test_ohne_werte_bleibt_alles_gleich():
    """Kein Wert zu setzen heißt: die Datei nicht anfassen. Byte für Byte."""
    assert godot_cfg.zusammenfuehren(VOSTOK, {}) == VOSTOK


def test_kommentare_und_reihenfolge_bleiben():
    text = "; von Hand gepflegt\n[a]\nx=1\n; dazwischen\ny=2\n"
    ergebnis = godot_cfg.zusammenfuehren(text, {"a": {"x": "9"}})
    assert "; von Hand gepflegt" in ergebnis
    assert "; dazwischen" in ergebnis
    assert ergebnis.index("x=9") < ergebnis.index("y=2")
