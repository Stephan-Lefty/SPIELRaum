"""Prüft die Zusage des Programms: hinterher ist es wieder wie vorher.

Das ist der Teil, an dem SPIELRaum steht oder fällt. Ein Spielstarter, der
eine Einstellungsdatei ändert und sie nicht zuverlässig zurückbringt, ist
schlimmer als gar keiner – denn dann merkt man den Schaden erst Wochen
später, wenn niemand mehr weiß, woher er kommt.
"""

import os

import pytest

from spielraum import stellschrauben, umgebung, zustand
from spielraum.profil import Dateiaenderung, Profil

VORHER = """[autoload_prepend]
ModLoader="*res://modloader.gd"

[autoload]

"""


@pytest.fixture
def eigene_ordner(tmp_path, monkeypatch):
    """Sicherungen und Journal in den Testordner umlenken."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "daten"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "lauf"))
    umgebung.ermitteln.cache_clear()
    return tmp_path


def profil_mit_datei(tmp_path) -> Profil:
    p = Profil(name="Testspiel", quelle=tmp_path / "x.toml", steam_app_id=42)
    p.dateien["override"] = Dateiaenderung(
        pfad="{spielordner}/override.cfg",
        art="godot-cfg",
        zusammenfuehren=True,
        werte={"rendering/renderer": {"rendering_method": '"mobile"'}},
    )
    return p


def test_anwenden_und_zuruecksetzen(eigene_ordner):
    """Der Normalfall: ändern, dann zurück – Byte für Byte."""
    spielordner = eigene_ordner / "spiel"
    spielordner.mkdir()
    datei = spielordner / "override.cfg"
    datei.write_text(VORHER, encoding="utf-8")

    profil = profil_mit_datei(eigene_ordner)
    journal = zustand.Journal(spiel=profil.name, pid=os.getpid())

    stellschrauben.dateien_anwenden(profil, journal, spielordner=spielordner)
    geaendert = datei.read_text(encoding="utf-8")
    assert 'rendering_method="mobile"' in geaendert
    assert 'ModLoader="*res://modloader.gd"' in geaendert  # Mods überleben

    stellschrauben.zuruecksetzen(journal)
    assert datei.read_text(encoding="utf-8") == VORHER


def test_absturz_wird_beim_naechsten_start_aufgeraeumt(eigene_ordner):
    """Der Fall, für den das Journal auf der Platte liegt.

    Nachgestellt wird ein harter Abbruch: Das Journal ist geschrieben, die
    Datei geändert, aber es läuft kein Prozess mehr, der zurücksetzen
    könnte. Beim nächsten Start muss SPIELRaum das allein aufräumen.
    """
    spielordner = eigene_ordner / "spiel"
    spielordner.mkdir()
    datei = spielordner / "override.cfg"
    datei.write_text(VORHER, encoding="utf-8")

    profil = profil_mit_datei(eigene_ordner)
    # PID 0 gibt es nicht - damit gilt das Journal als verwaist.
    journal = zustand.Journal(spiel=profil.name, pid=0)
    stellschrauben.dateien_anwenden(profil, journal, spielordner=spielordner)
    zustand.schreiben(journal)

    assert datei.read_text(encoding="utf-8") != VORHER  # Zustand nach »Absturz«

    verwaist = zustand.verwaiste_journale()
    assert len(verwaist) == 1
    for gefunden in verwaist:
        stellschrauben.zuruecksetzen(gefunden)

    assert datei.read_text(encoding="utf-8") == VORHER


def test_neu_angelegte_datei_wird_wieder_entfernt(eigene_ordner):
    """Gab es die Datei vorher nicht, darf hinterher keine dastehen."""
    spielordner = eigene_ordner / "spiel"
    spielordner.mkdir()
    datei = spielordner / "override.cfg"

    profil = profil_mit_datei(eigene_ordner)
    journal = zustand.Journal(spiel=profil.name, pid=os.getpid())

    stellschrauben.dateien_anwenden(profil, journal, spielordner=spielordner)
    assert datei.exists()

    stellschrauben.zuruecksetzen(journal)
    assert not datei.exists()


def test_journal_vor_der_aenderung(eigene_ordner):
    """Der Eintrag muss stehen, bevor die Datei angefasst wird.

    Andersherum wäre ein Absturz zwischen beiden Schritten nicht mehr
    aufzulösen: geänderte Datei, kein Hinweis worauf zurück.
    """
    spielordner = eigene_ordner / "spiel"
    spielordner.mkdir()
    (spielordner / "override.cfg").write_text(VORHER, encoding="utf-8")

    profil = profil_mit_datei(eigene_ordner)
    journal = zustand.Journal(spiel=profil.name, pid=os.getpid())
    stellschrauben.dateien_anwenden(profil, journal, spielordner=spielordner)

    assert len(journal.eintraege) == 1
    sicherung = journal.eintraege[0].vorher
    assert sicherung is not None
    from pathlib import Path
    assert Path(sicherung).read_text(encoding="utf-8") == VORHER


def test_umgebung_des_elternprozesses_bleibt_unberuehrt(eigene_ordner):
    """Die Umgebung wird kopiert, nicht verstellt.

    Damit kann diese Stellschraube gar nicht hängenbleiben - es gibt nichts
    zurückzusetzen.
    """
    profil = Profil(name="X", quelle=eigene_ordner / "x.toml")
    profil.variablen = {"SPIELRAUM_TESTWERT": "1"}
    vorher = dict(os.environ)

    gebaut = stellschrauben.umgebung_bauen(profil)

    assert gebaut["SPIELRAUM_TESTWERT"] == "1"
    assert "SPIELRAUM_TESTWERT" not in os.environ
    assert dict(os.environ) == vorher


def test_fehlender_spielordner_meldet_sich(eigene_ordner):
    """Deinstalliertes Spiel: klare Meldung statt Absturz im Nirgendwo."""
    profil = profil_mit_datei(eigene_ordner)
    journal = zustand.Journal(spiel=profil.name, pid=os.getpid())
    with pytest.raises(FileNotFoundError, match="nicht installiert"):
        stellschrauben.dateien_anwenden(profil, journal, spielordner=None)


def test_zuruecksetzen_macht_weiter_wenn_einer_fehlschlaegt(eigene_ordner):
    """Ein Aufräumer, der beim ersten Problem stehenbleibt, hinterlässt mehr
    Unordnung als einer, der weitermacht und berichtet."""
    spielordner = eigene_ordner / "spiel"
    spielordner.mkdir()
    gut = spielordner / "gut.cfg"
    gut.write_text(VORHER, encoding="utf-8")
    sicherung = eigene_ordner / "sicherung.cfg"
    sicherung.write_text(VORHER, encoding="utf-8")

    journal = zustand.Journal(spiel="X", pid=os.getpid())
    journal.vermerken("datei", str(spielordner / "weg.cfg"), str(eigene_ordner / "fehlt"))
    journal.vermerken("datei", str(gut), str(sicherung))
    gut.write_text("kaputt", encoding="utf-8")

    bericht = stellschrauben.zuruecksetzen(journal)

    assert any("FEHLT" in z for z in bericht)
    assert gut.read_text(encoding="utf-8") == VORHER  # trotzdem erledigt
