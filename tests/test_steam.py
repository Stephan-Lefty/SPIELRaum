"""Prüft den VDF-Leser und den Filter gegen Nicht-Spiele.

Die Beispiele sind gekürzte Abschriften echter Dateien vom 30.09.2026 – mit
den Eigenheiten, die echte Dateien haben: Tabulatoren als Einrückung,
Schlüssel und Klammer auf getrennten Zeilen, verschachtelte Blöcke.
"""

from spielraum import steam

LIBRARYFOLDERS = """"libraryfolders"
{
\t"0"
\t{
\t\t"path"\t\t"/home/wer/.local/share/Steam"
\t\t"label"\t\t""
\t\t"apps"
\t\t{
\t\t\t"228980"\t\t"158270267"
\t\t}
\t}
\t"1"
\t{
\t\t"path"\t\t"/mnt/Gaming/SteamLibrary"
\t\t"totalsize"\t\t"244995190784"
\t}
}
"""

MANIFEST = """"AppState"
{
\t"appid"\t\t"1963610"
\t"name"\t\t"Road to Vostok"
\t"installdir"\t\t"Road to Vostok"
\t"SizeOnDisk"\t\t"5942202400"
\t"UserConfig"
\t{
\t\t"language"\t\t"german"
\t}
}
"""


def test_verschachtelte_bloecke():
    daten = steam.vdf_lesen(LIBRARYFOLDERS)
    ordner = daten["libraryfolders"]
    assert ordner["0"]["path"] == "/home/wer/.local/share/Steam"
    assert ordner["1"]["path"] == "/mnt/Gaming/SteamLibrary"
    # Der Block innerhalb eines Blocks darf den äußeren nicht überschreiben.
    assert ordner["0"]["apps"]["228980"] == "158270267"


def test_manifest():
    zustand = steam.vdf_lesen(MANIFEST)["AppState"]
    assert zustand["appid"] == "1963610"
    assert zustand["name"] == "Road to Vostok"
    assert zustand["UserConfig"]["language"] == "german"


def test_leerer_wert():
    """»label« ist leer – das darf den Leser nicht aus dem Tritt bringen."""
    assert steam.vdf_lesen(LIBRARYFOLDERS)["libraryfolders"]["0"]["label"] == ""


def test_kaputte_zeilen_werden_uebersprungen():
    text = '"a"\n{\nMüll ohne Anführungszeichen\n"b"\t"1"\n}\n'
    assert steam.vdf_lesen(text) == {"a": {"b": "1"}}


def test_werkzeuge_gelten_nicht_als_spiele():
    """Ohne diesen Filter standen auf dem Testrechner 12 von 15 Einträgen
    zur Auswahl, die keine Spiele sind."""
    for name in (
        "Proton 9.0",
        "Proton Experimental",
        "Steam Linux Runtime 3.0 (sniper)",
        "Proton EasyAntiCheat Runtime",
        "Steamworks Shared",
        "Steam Controller Configs",
    ):
        assert steam.KEINE_SPIELE.match(name), f"{name} sollte gefiltert werden"


def test_echte_spiele_bleiben():
    for name in ("Road to Vostok", "Red Dead Redemption 2", "Atomfall", "Portal 2"):
        assert not steam.KEINE_SPIELE.match(name), f"{name} ist ein Spiel"


def test_groesse_lesbar():
    spiel = steam.Spiel(
        app_id=1, name="X", ordner=steam.Path("/tmp"), groesse=5942202400,
        bibliothek=steam.Path("/tmp"),
    )
    assert spiel.groesse_lesbar == "5,5 GB"
