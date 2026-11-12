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


# --- ecke_setzen -----------------------------------------------------------
#
# Die Profile dieses Projekts bestehen zu neun Zehnteln aus Kommentaren. Ein
# TOML-Schreiber würde sie löschen, und die Datei sähe danach gültig aus --
# dieselbe Falle wie bei der Vollsicherung am 03.11.2026. Deshalb prüfen
# diese Tests vor allem, was NICHT passiert.

MIT_KOMMENTAREN = '''[spiel]
# Warum dieses Spiel ein Profil hat.
name = "Testspiel"
steam_app_id = 42

# Ein Block, der erhalten bleiben muss.
# Zweite Zeile davon.
[messen]
mangohud = true
ecke = "top-left"  # und ein Kommentar am Zeilenende
deckkraft = 0.25
'''


def test_ecke_ersetzen_laesst_alle_kommentare_stehen(tmp_path):
    datei = tmp_path / "p.toml"
    datei.write_text(MIT_KOMMENTAREN, encoding="utf-8")

    vorher = profil.ecke_setzen(datei, "bottom-right")
    assert vorher == "top-left"

    text = datei.read_text(encoding="utf-8")
    assert profil.laden(datei).overlay_ecke == "bottom-right"
    assert text.count("#") == MIT_KOMMENTAREN.count("#"), "Kommentare fehlen"
    assert "und ein Kommentar am Zeilenende" in text
    assert "Ein Block, der erhalten bleiben muss." in text
    assert len(text.splitlines()) == len(MIT_KOMMENTAREN.splitlines())
    # Die anderen Werte des Abschnitts bleiben unangetastet.
    assert profil.laden(datei).overlay_deckkraft == 0.25


def test_ecke_anlegen_wenn_sie_fehlt(tmp_path):
    datei = tmp_path / "p.toml"
    datei.write_text('[spiel]\nname = "T"\nsteam_app_id = 1\n\n'
                     '[messen]\nmangohud = true\n', encoding="utf-8")

    assert profil.ecke_setzen(datei, "middle-left") == ""
    assert profil.laden(datei).overlay_ecke == "middle-left"
    assert "mangohud = true" in datei.read_text(encoding="utf-8")


def test_messen_abschnitt_wird_angelegt(tmp_path):
    """Ein Profil ohne [messen] ist zulässig -- dann muss der Abschnitt
    entstehen, und zwar ohne an den letzten Wert zu kleben."""
    datei = tmp_path / "p.toml"
    datei.write_text('[spiel]\nname = "T"\nsteam_app_id = 1\n', encoding="utf-8")

    assert profil.ecke_setzen(datei, "top-right") == ""
    assert profil.laden(datei).overlay_ecke == "top-right"
    zeilen = datei.read_text(encoding="utf-8").splitlines()
    assert "[messen]" in zeilen
    assert zeilen[zeilen.index("[messen]") - 1] == "", \
        "der Abschnitt klebt am letzten Wert"


def test_ecke_nur_im_messen_abschnitt(tmp_path):
    """Ein »ecke« in einem anderen Abschnitt darf nicht angefasst werden."""
    datei = tmp_path / "p.toml"
    datei.write_text('[spiel]\nname = "T"\nsteam_app_id = 1\n'
                     'ecke = "irgendwas"\n\n'
                     '[messen]\nmangohud = true\n', encoding="utf-8")

    profil.ecke_setzen(datei, "bottom-left")
    text = datei.read_text(encoding="utf-8")
    assert 'ecke = "irgendwas"' in text, "der fremde Schlüssel wurde verändert"
    assert profil.laden(datei).overlay_ecke == "bottom-left"


def test_unsinnige_ecke_laesst_die_datei_unberuehrt(tmp_path):
    datei = tmp_path / "p.toml"
    datei.write_text(MIT_KOMMENTAREN, encoding="utf-8")
    with pytest.raises(profil.ProfilFehler, match="MangoHud kennt"):
        profil.ecke_setzen(datei, "oben-links")
    assert datei.read_text(encoding="utf-8") == MIT_KOMMENTAREN


def test_crlf_bleibt_crlf(tmp_path):
    """Am 09.11.2026 hat eine Bearbeitung 68 CRLF in LF verwandelt. Hier
    sind es eigene Dateien, aber der Reflex bleibt."""
    datei = tmp_path / "p.toml"
    datei.write_bytes(MIT_KOMMENTAREN.replace("\n", "\r\n").encode("utf-8"))

    profil.ecke_setzen(datei, "middle-right")
    roh = datei.read_bytes()
    assert b"\r\n" in roh
    assert roh.count(b"\n") == roh.count(b"\r\n"), "ein Zeilenende wurde gewandelt"
