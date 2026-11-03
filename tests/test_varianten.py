"""Prüft das Umschalten zwischen den Richtungen.

Der wichtigste Test ist ``test_sicherung_bleibt_die_erste``. Wer dreimal
umschaltet und dann zurück will, muss dort landen, wo er angefangen hat –
nicht bei der vorletzten Variante. Eine Sicherung, die bei jeder Umstellung
überschrieben wird, ist keine.
"""

import pytest

from spielraum import umgebung, varianten
from spielraum.profil import Dateiaenderung, Profil, Variante

AUSGANG = '''[gd_resource type="Resource" format=3]

[sub_resource type="InputEventKey" id="A"]
keycode = 4194322

[resource]
lighting = 3
antialiasing = 3
sharpness = 1.0
'''


@pytest.fixture
def aufbau(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "daten"))
    umgebung.ermitteln.cache_clear()

    spielordner = tmp_path / "spiel"
    spielordner.mkdir()
    datei = spielordner / "Preferences.tres"
    datei.write_text(AUSGANG, encoding="utf-8")

    p = Profil(name="Testspiel", quelle=tmp_path / "x.toml", steam_app_id=42)
    p.dateien["grafik"] = Dateiaenderung(
        pfad="{spielordner}/Preferences.tres", art="godot-tres")
    p.varianten = {
        "optik": Variante("optik", "hübsch",
                          {"grafik": {"lighting": 3, "antialiasing": 3}}),
        "mitte": Variante("mitte", "dazwischen",
                          {"grafik": {"lighting": 2, "antialiasing": 2}}),
        "leistung": Variante("leistung", "flüssig",
                             {"grafik": {"lighting": 1, "antialiasing": 1}}),
    }
    return p, spielordner, datei


def test_zuruecksetzen_laesst_dem_spiel_seine_eigenen_werte(aufbau):
    """Der Fehler vom 03.11.2026, hier im Variantenweg.

    Zurückgesetzt wurde mit ``shutil.copy2`` der ganzen Sicherung – und die
    liegt vom Tag der *ersten* Umstellung. Alles, was das Spiel seither
    selbst in dieselbe Datei geschrieben hat, war damit weg. Bei Road to
    Vostok waren das die Tastenbelegung, die Lautstärken und das Blickfeld,
    und weil jedes Spielende denselben Stand zurückholte, konnte die Datei
    fünf Wochen lang gar nicht mehr anders werden.

    Hier spielt der Test das nach: umschalten, dann schreibt »das Spiel«
    etwas Eigenes, dann zurücksetzen.
    """
    profil, spielordner, datei = aufbau
    varianten.anwenden(profil, "leistung", spielordner=spielordner)

    # Jetzt schreibt das Spiel selbst - eine Taste und eine Lautstärke.
    text = datei.read_text(encoding="utf-8")
    text = text.replace("keycode = 4194322", "keycode = 4194320")
    text = text.replace("[resource]", "[resource]\nmusicVolume = 0.1")
    datei.write_text(text, encoding="utf-8")

    varianten.zuruecksetzen(profil, spielordner=spielordner)
    danach = datei.read_text(encoding="utf-8")

    # Unsere Werte sind zurück...
    assert "lighting = 3" in danach
    assert "antialiasing = 3" in danach
    # ...und das Spiel hat behalten, was ihm gehört.
    assert "keycode = 4194320" in danach, "die Taste des Spiels wurde überschrieben"
    assert "musicVolume = 0.1" in danach, "die Lautstärke des Spiels ist weg"


def test_zuruecksetzen_fasst_nur_profilschluessel_an(aufbau):
    """Was in keiner Variante und keinem [dateien]-Block steht, bleibt.

    ``sharpness`` steht im Ausgangstext, aber in keinem Profilwert. Selbst
    wenn das Spiel es verstellt, ist das nicht unsere Angelegenheit.
    """
    profil, spielordner, datei = aufbau
    varianten.anwenden(profil, "leistung", spielordner=spielordner)
    datei.write_text(
        datei.read_text(encoding="utf-8").replace("sharpness = 1.0",
                                                  "sharpness = 0.5"),
        encoding="utf-8")

    varianten.zuruecksetzen(profil, spielordner=spielordner)
    assert "sharpness = 0.5" in datei.read_text(encoding="utf-8")


def test_anwenden_aendert_die_werte(aufbau):
    p, ordner, datei = aufbau
    varianten.anwenden(p, "leistung", spielordner=ordner)
    inhalt = datei.read_text(encoding="utf-8")
    assert "lighting = 1" in inhalt
    assert "antialiasing = 1" in inhalt
    assert "keycode = 4194322" in inhalt  # Tastenbelegung unberührt


def test_sicherung_bleibt_die_erste(aufbau):
    """Dreimal umschalten, dann zurück – und zwar ganz zurück."""
    p, ordner, datei = aufbau
    varianten.anwenden(p, "leistung", spielordner=ordner)
    varianten.anwenden(p, "mitte", spielordner=ordner)
    varianten.anwenden(p, "leistung", spielordner=ordner)

    varianten.zuruecksetzen(p, spielordner=ordner)
    assert datei.read_text(encoding="utf-8") == AUSGANG


def test_aktuelle_erkennt_die_variante(aufbau):
    p, ordner, datei = aufbau
    assert varianten.aktuelle(p, spielordner=ordner) == "optik"  # Ausgangslage
    varianten.anwenden(p, "mitte", spielordner=ordner)
    assert varianten.aktuelle(p, spielordner=ordner) == "mitte"


def test_aktuelle_meldet_fremde_werte(aufbau):
    """Wer im Spielmenü etwas eigenes einstellt, soll nicht fälschlich einer
    Variante zugeordnet werden – für die Messfahrt ist das entscheidend."""
    p, ordner, datei = aufbau
    datei.write_text(AUSGANG.replace("lighting = 3", "lighting = 4"), encoding="utf-8")
    assert varianten.aktuelle(p, spielordner=ordner) is None


def test_unbekannte_variante(aufbau):
    p, ordner, _ = aufbau
    with pytest.raises(varianten.VariantenFehler, match="kennt dieses Profil nicht"):
        varianten.anwenden(p, "turbo", spielordner=ordner)


def test_fehlende_datei_wird_erklaert(aufbau):
    p, ordner, datei = aufbau
    datei.unlink()
    with pytest.raises(varianten.VariantenFehler, match="beim ersten Start"):
        varianten.anwenden(p, "mitte", spielordner=ordner)


def test_zuruecksetzen_ohne_sicherung(aufbau):
    p, ordner, _ = aufbau
    bericht = varianten.zuruecksetzen(p, spielordner=ordner)
    assert "nie eine Variante" in bericht[0]


def test_zweimal_dieselbe_variante(aufbau):
    p, ordner, _ = aufbau
    varianten.anwenden(p, "mitte", spielordner=ordner)
    bericht = varianten.anwenden(p, "mitte", spielordner=ordner)
    assert any("stand schon so" in z for z in bericht)
