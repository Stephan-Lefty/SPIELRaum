"""Prüft das Profilformat – vor allem dort, wo es Nein sagen muss."""

import pytest

from spielraum import profil

KOPF = '[spiel]\nname = "Testspiel"\nsteam_app_id = 42\n'


def schreiben(ordner, inhalt):
    pfad = ordner / "test.toml"
    pfad.write_text(inhalt, encoding="utf-8")
    return pfad


def test_kleinstes_profil(tmp_path):
    p = profil.laden(schreiben(tmp_path, KOPF))
    assert p.name == "Testspiel"
    assert p.steam_app_id == 42
    assert p.gamemode is True  # Standard


def test_fester_pfad_wird_abgelehnt(tmp_path):
    """Der Fall, der nach einer Neuinstallation kaputtgeht.

    Steam legt ein neu geladenes Spiel in die Bibliothek, wo Platz ist –
    nicht zwingend dorthin, wo es vorher lag. Ein Profil mit festem Pfad
    zeigt dann ins Leere oder, schlimmer, auf ein anderes Spiel.
    """
    inhalt = KOPF + '\n[dateien.x]\npfad = "/mnt/HDD-1.0TB/Spiel/override.cfg"\n'
    with pytest.raises(profil.ProfilFehler, match="fester Pfad"):
        profil.laden(schreiben(tmp_path, inhalt))


def test_platzhalter_ist_erlaubt(tmp_path):
    inhalt = KOPF + '\n[dateien.x]\npfad = "{spielordner}/override.cfg"\n'
    p = profil.laden(schreiben(tmp_path, inhalt))
    assert p.dateien["x"].pfad == "{spielordner}/override.cfg"
    assert p.dateien["x"].zusammenfuehren is True  # Standard, und gut so


def test_unbekannte_dateiart(tmp_path):
    inhalt = KOPF + '\n[dateien.x]\npfad = "{spielordner}/a.ini"\nart = "ini"\n'
    with pytest.raises(profil.ProfilFehler, match="kennt SPIELRaum nicht"):
        profil.laden(schreiben(tmp_path, inhalt))


def test_unsinniger_variablenname(tmp_path):
    inhalt = KOPF + '\n[umgebung]\n"böser name" = "1"\n'
    with pytest.raises(profil.ProfilFehler, match="zulässiger Name"):
        profil.laden(schreiben(tmp_path, inhalt))


def test_zahlen_werden_zu_text(tmp_path):
    """TOML kennt Zahlen, die Prozessumgebung nicht."""
    inhalt = KOPF + "\n[umgebung]\nDXVK_FRAME_RATE = 60\nMANGOHUD = true\n"
    p = profil.laden(schreiben(tmp_path, inhalt))
    assert p.variablen["DXVK_FRAME_RATE"] == "60"
    assert p.variablen["MANGOHUD"] == "true"


def test_governor_muss_plausibel_sein(tmp_path):
    inhalt = KOPF + '\n[system]\ncpu_governor = "; rm -rf /"\n'
    with pytest.raises(profil.ProfilFehler, match="Governor"):
        profil.laden(schreiben(tmp_path, inhalt))


def test_fehlender_name(tmp_path):
    with pytest.raises(profil.ProfilFehler, match=r"\[spiel\]"):
        profil.laden(schreiben(tmp_path, '[system]\ngamemode = true\n'))


def test_kaputtes_toml(tmp_path):
    with pytest.raises(profil.ProfilFehler, match="gültiges TOML"):
        profil.laden(schreiben(tmp_path, '[spiel\nname = "x"\n'))
