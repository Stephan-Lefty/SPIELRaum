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


# --- Die Aufnahmen aus den Spielen -----------------------------------------
#
# Steam legt sie unter userdata/<Konto>/760/remote/<App-ID>/screenshots ab.
# Die 760 ist Steams eigene App-Nummer für die Aufnahmefunktion.


def _bilderbaum(wurzel, konto, app_id, anzahl, endung="jpg"):
    ordner = wurzel / "userdata" / str(konto) / "760" / "remote" / str(app_id) / "screenshots"
    ordner.mkdir(parents=True, exist_ok=True)
    for n in range(anzahl):
        (ordner / f"{app_id}_2026111{n}.{endung}").write_bytes(b"\xff\xd8")
    return ordner


def test_bilderordner_wird_gefunden(tmp_path, monkeypatch):
    wurzel = tmp_path / "Steam"
    _bilderbaum(wurzel, 154920572, 1963610, 13)
    monkeypatch.setattr(steam, "steam_wurzeln", lambda: [wurzel])

    assert len(steam.bilderordner(1963610)) == 1
    assert steam.bilder_zaehlen(1963610) == 13


def test_verweis_auf_dieselbe_wurzel_zaehlt_nicht_doppelt(tmp_path, monkeypatch):
    """Die Falle vom 12.11.2026.

    ``~/.steam/steam`` ist auf diesem Rechner ein Verweis auf
    ``~/.local/share/Steam``, und beide stehen in ``steam_wurzeln()``. Beim
    ersten Versuch meldete SPIELRaum vierzig Aufnahmen, wo zwanzig lagen.
    """
    echt = tmp_path / "local" / "Steam"
    _bilderbaum(echt, 154920572, 801800, 20)
    verweis = tmp_path / "dotsteam"
    verweis.parent.mkdir(parents=True, exist_ok=True)
    verweis.symlink_to(echt, target_is_directory=True)
    monkeypatch.setattr(steam, "steam_wurzeln", lambda: [verweis, echt])

    assert len(steam.bilderordner(801800)) == 1
    assert steam.bilder_zaehlen(801800) == 20


def test_zwei_konten_geben_zwei_ordner(tmp_path, monkeypatch):
    """Zwei Steam-Konten auf einem Rechner sind kein Fehler."""
    wurzel = tmp_path / "Steam"
    _bilderbaum(wurzel, 111, 1963610, 3)
    _bilderbaum(wurzel, 222, 1963610, 4)
    monkeypatch.setattr(steam, "steam_wurzeln", lambda: [wurzel])

    assert len(steam.bilderordner(1963610)) == 2
    assert steam.bilder_zaehlen(1963610) == 7


def test_leerer_ordner_gilt_als_keiner(tmp_path, monkeypatch):
    """Steam legt den Ordner schon beim ersten Spielstart an.

    »Ordner vorhanden« sagt also nichts -- und ein Knopf, der ein leeres
    Fenster öffnet, ist schlimmer als ein grauer.
    """
    wurzel = tmp_path / "Steam"
    _bilderbaum(wurzel, 111, 1203620, 0)
    monkeypatch.setattr(steam, "steam_wurzeln", lambda: [wurzel])

    assert steam.bilderordner(1203620) == []
    assert steam.bilder_zaehlen(1203620) == 0


def test_ohne_userdata_kein_absturz(tmp_path, monkeypatch):
    """Eine Steam-Wurzel, die es gar nicht gibt, ist der Normalfall:
    ``steam_wurzeln()`` nennt vier Pfade, von denen höchstens einer stimmt."""
    monkeypatch.setattr(steam, "steam_wurzeln",
                        lambda: [tmp_path / "gibtsnicht", tmp_path / "leer"])
    (tmp_path / "leer").mkdir()
    assert steam.bilderordner(1963610) == []
