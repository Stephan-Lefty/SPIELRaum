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


# --- messen.deckkraft ------------------------------------------------------


def test_deckkraft_wird_gelesen(tmp_path):
    datei = tmp_path / "p.toml"
    datei.write_text(KOPF + "\n[messen]\ndeckkraft = 0.1\n", encoding="utf-8")
    assert profil.laden(datei).overlay_deckkraft == 0.1


def test_deckkraft_null_ist_erlaubt(tmp_path):
    """In TOML ist »0« eine Ganzzahl. Daran darf kein Profil scheitern."""
    datei = tmp_path / "p.toml"
    datei.write_text(KOPF + "\n[messen]\ndeckkraft = 0\n", encoding="utf-8")
    assert profil.laden(datei).overlay_deckkraft == 0.0


def test_deckkraft_ausserhalb_des_bereichs_wird_abgewiesen(tmp_path):
    """Lieber eine Fehlermeldung als eine Anzeige, die niemand sieht."""
    datei = tmp_path / "p.toml"
    datei.write_text(KOPF + "\n[messen]\ndeckkraft = 50\n", encoding="utf-8")
    with pytest.raises(profil.ProfilFehler, match="0 .*bis 1"):
        profil.laden(datei)


def test_deckkraft_als_text_wird_abgewiesen(tmp_path):
    datei = tmp_path / "p.toml"
    datei.write_text(KOPF + '\n[messen]\ndeckkraft = "halb"\n', encoding="utf-8")
    with pytest.raises(profil.ProfilFehler, match="Zahl"):
        profil.laden(datei)


def test_deckkraft_als_wahrheitswert_wird_abgewiesen(tmp_path):
    """``True`` ist in Python eine 1 und würde sonst stillschweigend als
    »voll deckend« durchgehen."""
    datei = tmp_path / "p.toml"
    datei.write_text(KOPF + "\n[messen]\ndeckkraft = true\n", encoding="utf-8")
    with pytest.raises(profil.ProfilFehler, match="Zahl"):
        profil.laden(datei)
