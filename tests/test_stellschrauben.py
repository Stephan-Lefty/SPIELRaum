"""Prüft die Zusage des Programms: hinterher ist es wieder wie vorher.

Das ist der Teil, an dem SPIELRaum steht oder fällt. Ein Spielstarter, der
eine Einstellungsdatei ändert und sie nicht zuverlässig zurückbringt, ist
schlimmer als gar keiner – denn dann merkt man den Schaden erst Wochen
später, wenn niemand mehr weiß, woher er kommt.
"""

import json
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


TRES_VORHER = '''[gd_resource type="Resource" format=3]

[sub_resource type="InputEventKey" id="A"]
keycode = 4194322

[resource]
lighting = 3
antialiasing = 3
musicVolume = 1.0
'''


def profil_mit_tres(tmp_path) -> Profil:
    p = Profil(name="Vostokartig", quelle=tmp_path / "x.toml", steam_app_id=43)
    p.dateien["grafik"] = Dateiaenderung(
        pfad="{spielordner}/Preferences.tres",
        art="godot-tres",
        werte={"lighting": 1, "antialiasing": 1},
    )
    return p


def test_zuruecksetzen_laesst_dem_spiel_seine_eigenen_werte(eigene_ordner):
    """Der Fehler vom 03.11.2026 – der eigentliche Grund für Journalfassung 2.

    Zurückgesetzt wurde die **ganze** Sicherung. Damit verschwand alles, was
    das Spiel während des Laufs selbst in dieselbe Datei geschrieben hatte.
    Bei Road to Vostok stehen in der Preferences.tres neben den
    Grafikeinstellungen die Tastenbelegung, die Lautstärken und das
    Blickfeld – und weil jeder Lauf denselben Stand zurückholte, konnte die
    Datei fünf Wochen lang gar nicht mehr anders werden. Die Umbelegung im
    Spielmenü vom 23.10.2026 war deshalb am nächsten Tag wieder weg.
    """
    spielordner = eigene_ordner / "spiel"
    spielordner.mkdir()
    datei = spielordner / "Preferences.tres"
    datei.write_text(TRES_VORHER, encoding="utf-8")

    profil = profil_mit_tres(eigene_ordner)
    journal = zustand.Journal(spiel=profil.name, pid=os.getpid())
    stellschrauben.dateien_anwenden(profil, journal, spielordner=spielordner)
    assert "lighting = 1" in datei.read_text(encoding="utf-8")

    # Das Spiel läuft und schreibt selbst: eine Taste und eine Lautstärke.
    text = datei.read_text(encoding="utf-8")
    text = text.replace("keycode = 4194322", "keycode = 4194320")
    text = text.replace("musicVolume = 1.0", "musicVolume = 0.1")
    datei.write_text(text, encoding="utf-8")

    stellschrauben.zuruecksetzen(journal)
    danach = datei.read_text(encoding="utf-8")

    assert "lighting = 3" in danach, "unsere Änderung kam nicht zurück"
    assert "antialiasing = 3" in danach
    assert "keycode = 4194320" in danach, "die Taste des Spiels wurde überschrieben"
    assert "musicVolume = 0.1" in danach, "die Lautstärke des Spiels ist weg"


def test_typ_bleibt_beim_zuruecksetzen_erhalten(eigene_ordner):
    """``1.0`` muss ``1.0`` bleiben, nicht ``1`` werden.

    Die alten Werte stehen als Text im Journal, genau wie sie in der Datei
    standen. Eine Umwandlung nach Zahl und zurück würde den Typ ändern, auf
    den sich GDScript verlässt.
    """
    spielordner = eigene_ordner / "spiel"
    spielordner.mkdir()
    datei = spielordner / "Preferences.tres"
    datei.write_text(TRES_VORHER, encoding="utf-8")

    profil = profil_mit_tres(eigene_ordner)
    profil.dateien["grafik"].werte = {"musicVolume": 0.5}
    journal = zustand.Journal(spiel=profil.name, pid=os.getpid())

    stellschrauben.dateien_anwenden(profil, journal, spielordner=spielordner)
    assert "musicVolume = 0.5" in datei.read_text(encoding="utf-8")

    stellschrauben.zuruecksetzen(journal)
    assert "musicVolume = 1.0" in datei.read_text(encoding="utf-8")


def test_altes_journal_wird_noch_aufgeraeumt(eigene_ordner):
    """Netz 4 muss auch hinter der *vorigen* Fassung aufräumen.

    Ein Journal der Fassung 1 kennt keine Einzelwerte, nur den Pfad der
    Vollsicherung. Würde ``lesen`` es verwerfen, bliebe eine Änderung nach
    einem Absturz für immer stehen. Beim Sprung auf Fassung 2 am 03.11.2026
    lag auf dem Rechner tatsächlich so ein Journal.
    """
    spielordner = eigene_ordner / "spiel"
    spielordner.mkdir()
    datei = spielordner / "override.cfg"
    datei.write_text(VORHER, encoding="utf-8")

    sicherung = eigene_ordner / "sicherung.cfg"
    sicherung.write_text(VORHER, encoding="utf-8")
    datei.write_text(VORHER + 'etwas="verstellt"\n', encoding="utf-8")

    pfad = zustand.journal_pfad("Altspiel")
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_text(json.dumps({
        "spiel": "Altspiel",
        "pid": 0,
        "fassung": 1,
        "eintraege": [{"stellschraube": "datei", "ziel": str(datei),
                       "vorher": str(sicherung), "nachher": None}],
    }), encoding="utf-8")

    journal = zustand.lesen(pfad)
    assert journal is not None, "ein Journal der Fassung 1 muss lesbar bleiben"

    bericht = stellschrauben.zuruecksetzen(journal)
    assert datei.read_text(encoding="utf-8") == VORHER
    assert any("ganze Datei" in z for z in bericht), \
        "der alte Weg soll im Bericht erkennbar sein"


def test_angelegter_schluessel_wird_wieder_entfernt(eigene_ordner):
    """Was vorher nicht dastand, geht nicht auf einen alten Wert zurück.

    Es muss weg. Sonst bliebe nach dem Zurücksetzen eine Zeile stehen, die
    SPIELRaum selbst erfunden hat – und zwar gerade dann, wenn sonst nichts
    mehr an die Vollsicherung erinnert.
    """
    spielordner = eigene_ordner / "spiel"
    spielordner.mkdir()
    datei = spielordner / "override.cfg"
    datei.write_text(VORHER, encoding="utf-8")

    profil = profil_mit_datei(eigene_ordner)
    journal = zustand.Journal(spiel=profil.name, pid=os.getpid())
    stellschrauben.dateien_anwenden(profil, journal, spielordner=spielordner)

    # Das Spiel schreibt daneben etwas Eigenes in einen eigenen Abschnitt.
    datei.write_text(datei.read_text(encoding="utf-8")
                     + '\n[display]\nwidth=1920\n', encoding="utf-8")

    stellschrauben.zuruecksetzen(journal)
    danach = datei.read_text(encoding="utf-8")

    assert "rendering_method" not in danach, "unsere Zeile blieb stehen"
    assert "[rendering/renderer]" not in danach, "unser Abschnitt blieb stehen"
    assert "width=1920" in danach, "der Abschnitt des Spiels ist weg"
    assert 'ModLoader="*res://modloader.gd"' in danach


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


def test_profil_argumente_landen_am_spiel(eigene_ordner):
    """Der Fehler, der bis 0.3.0 drinsteckte.

    »start.argumente« wurde gelesen, geprüft und angezeigt – nur nie
    angewendet. Wer damit den Renderer umstellte, maß anschließend zweimal
    dasselbe und hätte geschlossen, die Umstellung bringe nichts.
    """
    profil = Profil(name="X", quelle=eigene_ordner / "x.toml")
    profil.gamemode = False
    profil.nicht_stoeren = False
    profil.argumente = ["--rendering-driver", "vulkan"]

    voll = stellschrauben.befehl_umhuellen(profil, ["/pfad/proton", "run", "RTV.exe"])

    assert voll == ["/pfad/proton", "run", "RTV.exe", "--rendering-driver", "vulkan"]


def test_argumente_stehen_hinter_dem_spiel_nicht_davor(eigene_ordner):
    """Reihenfolge ist hier alles: Was vor dem Programmnamen steht, gehört
    noch zu Proton und nicht zum Spiel."""
    profil = Profil(name="X", quelle=eigene_ordner / "x.toml")
    profil.gamemode = False
    profil.nicht_stoeren = False
    profil.argumente = ["--fullscreen"]

    voll = stellschrauben.befehl_umhuellen(profil, ["proton", "run", "spiel.exe"])

    assert voll.index("--fullscreen") > voll.index("spiel.exe")


def test_ohne_argumente_bleibt_der_befehl_unveraendert(eigene_ordner):
    profil = Profil(name="X", quelle=eigene_ordner / "x.toml")
    profil.gamemode = False
    profil.nicht_stoeren = False

    assert stellschrauben.befehl_umhuellen(profil, ["a", "b"]) == ["a", "b"]
