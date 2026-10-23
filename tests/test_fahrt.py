"""Prüft die Messfahrt – vor allem dort, wo sie etwas verweigern muss.

Die Messfahrt ist der einzige Teil von SPIELRaum, der mehrere Spielstarts
überdauert. Zwischen zwei Läufen existiert kein Prozess; alles, was sie
weiß, steht in einer Datei. Entsprechend drehen sich die meisten Tests um
diese Datei und darum, was passiert, wenn ein Lauf nicht zählt.
"""

import json

import pytest

from spielraum import fahrt
from spielraum.messen import Kennzahlen


@pytest.fixture(autouse=True)
def _eigenes_verzeichnis(tmp_path, monkeypatch):
    """Nicht in die echten Akten des Benutzers schreiben."""
    monkeypatch.setattr(fahrt.umgebung, "daten_verzeichnis", lambda: tmp_path)
    yield


def neue(varianten=("optik", "ausgeglichen", "leistung")) -> fahrt.Fahrt:
    return fahrt.Fahrt(spiel="Testspiel", steam_app_id=42,
                       varianten=list(varianten))


def kennzahlen(dauer=700.0, ladezeit=0.0, mittel=50.0, tief=25.0) -> Kennzahlen:
    return Kennzahlen(mittel=mittel, tief_1=tief, tief_01=tief / 2,
                      stichproben=int(dauer * 10), dauer=dauer, verworfen=0,
                      ladezeit=ladezeit)


# --- Der Ablauf ------------------------------------------------------------


def test_erste_variante_ist_die_naechste():
    assert neue().naechste == "optik"


def test_nach_einem_lauf_kommt_die_zweite():
    f = neue()
    f.vermerken(fahrt.Lauf(variante="optik", messdatei="a.csv", tief_1=20))
    assert f.naechste == "ausgeglichen"
    assert f.stand == "1 von 3"


def test_fertig_wenn_alle_zaehlen():
    f = neue()
    for name in f.varianten:
        f.vermerken(fahrt.Lauf(variante=name, messdatei=f"{name}.csv"))
    assert f.fertig
    assert f.naechste is None


def test_verworfener_lauf_wird_wiederholt():
    """Der entscheidende Fall: Ein zu kurzer Lauf darf nicht weiterzählen.

    Sonst hätte man am Ende drei Zahlen, von denen eine aus fünf Minuten
    stammt – und die läge systematisch zu hoch.
    """
    f = neue()
    f.vermerken(fahrt.Lauf(variante="optik", verworfen="zu kurz"))
    assert f.naechste == "optik"
    assert f.stand == "0 von 3"


def test_wiederholung_ersetzt_den_fehlversuch():
    """Sonst sammelt sich bei jedem Anlauf ein weiterer Eintrag an."""
    f = neue()
    f.vermerken(fahrt.Lauf(variante="optik", verworfen="zu kurz"))
    f.vermerken(fahrt.Lauf(variante="optik", verworfen="auch zu kurz"))
    f.vermerken(fahrt.Lauf(variante="optik", messdatei="endlich.csv"))
    assert len(f.laeufe) == 1
    assert f.laeufe[0].zaehlt


# --- Bewerten --------------------------------------------------------------


def test_beste_nach_tiefstwert_nicht_nach_mittel():
    """Der Mittelwert sagt, wie es im Schnitt aussah. Der 1-%-Tiefstwert
    sagt, wie schlecht es in den schlechtesten Momenten wurde – und die
    nimmt man als Ruckeln wahr.
    """
    f = neue()
    f.vermerken(fahrt.Lauf(variante="optik", messdatei="a", mittel=60, tief_1=12))
    f.vermerken(fahrt.Lauf(variante="leistung", messdatei="b", mittel=48, tief_1=31))
    assert f.beste().variante == "leistung"


def test_ohne_zaehlenden_lauf_gibt_es_keine_beste():
    f = neue()
    f.vermerken(fahrt.Lauf(variante="optik", verworfen="nichts gemessen"))
    assert f.beste() is None


def test_zu_kurzer_lauf_wird_begruendet():
    grund = fahrt.pruefen(kennzahlen(dauer=300.0))
    assert grund
    assert "5.0 Minuten" in grund
    assert "60,6" in grund  # die Messung, aus der die Regel stammt


def test_ladezeit_zaehlt_nicht_als_spielzeit():
    """Elf Minuten, davon zwei Minuten Laden, sind neun Minuten Spielzeit."""
    assert fahrt.pruefen(kennzahlen(dauer=660.0, ladezeit=120.0))


def test_langer_lauf_zaehlt():
    assert fahrt.pruefen(kennzahlen(dauer=700.0)) == ""


def test_ohne_messung_kein_lauf():
    assert "MangoHud" in fahrt.pruefen(None)


# --- Auf der Platte --------------------------------------------------------


def test_schreiben_und_lesen():
    f = neue()
    f.vermerken(fahrt.Lauf(variante="optik", messdatei="a.csv", mittel=47.5))
    fahrt.schreiben(f)
    zurueck = fahrt.lesen(42)
    assert zurueck is not None
    assert zurueck.spiel == "Testspiel"
    assert zurueck.laeufe[0].mittel == 47.5
    assert zurueck.naechste == "ausgeglichen"


def test_ohne_akte_kein_ergebnis():
    assert fahrt.lesen(999) is None


def test_kaputte_akte_wird_nicht_geraten():
    """Lieber keine Fahrt als eine halb verstandene.

    Eine Akte, die falsch gelesen wird, schickt den nächsten Lauf auf die
    falsche Variante – und das merkt niemand.
    """
    fahrt.akte_pfad(42).write_text("{kein json", encoding="utf-8")
    assert fahrt.lesen(42) is None


def test_fremde_fassung_wird_abgelehnt():
    fahrt.akte_pfad(42).write_text(
        json.dumps({"spiel": "X", "steam_app_id": 42, "varianten": [],
                    "fassung": 99}), encoding="utf-8")
    assert fahrt.lesen(42) is None


def test_entfernen():
    fahrt.schreiben(neue())
    fahrt.entfernen(42)
    assert fahrt.lesen(42) is None


def test_entfernen_ohne_akte_ist_kein_fehler():
    fahrt.entfernen(999)  # darf nicht werfen


def test_alle_findet_mehrere():
    fahrt.schreiben(neue())
    zweite = neue()
    zweite.steam_app_id = 43
    fahrt.schreiben(zweite)
    assert {f.steam_app_id for f in fahrt.alle()} == {42, 43}


def test_alle_uebergeht_fremde_dateien():
    """Im Ordner kann anderes liegen – das darf nicht stören."""
    fahrt.fahrten_verzeichnis().joinpath("notizen.json").write_text("{}")
    fahrt.schreiben(neue())
    assert [f.steam_app_id for f in fahrt.alle()] == [42]


# --- Automatik -------------------------------------------------------------


def test_abgeschlossene_fahrt_bleibt_liegen():
    """Als Ergebnisspeicher und als Merker.

    Ohne das begänne bei eingeschalteter Automatik nach jedem Verwerfen
    sofort die nächste Fahrt – man käme nie zum Spielen.
    """
    f = neue()
    for name in f.varianten:
        f.vermerken(fahrt.Lauf(variante=name, messdatei=f"{name}.csv"))
    f.abschliessen("leistung")
    fahrt.schreiben(f)

    zurueck = fahrt.lesen(42)
    assert zurueck.abgeschlossen
    assert zurueck.uebernommen == "leistung"


def test_abbrechen_merkt_sich_das_auch():
    """Auch eine verworfene Fahrt darf nicht sofort neu beginnen."""
    f = neue()
    f.abschliessen()
    fahrt.schreiben(f)
    assert fahrt.lesen(42).abgeschlossen
    assert fahrt.lesen(42).uebernommen == ""


def test_profil_schalter_ist_aus_wenn_nichts_dasteht(tmp_path):
    from spielraum import profil
    pfad = tmp_path / "t.toml"
    pfad.write_text('[spiel]\nname = "X"\n', encoding="utf-8")
    assert profil.laden(pfad).fahrt_automatisch is False


def test_profil_schalter_laesst_sich_setzen(tmp_path):
    from spielraum import profil
    pfad = tmp_path / "t.toml"
    pfad.write_text('[spiel]\nname = "X"\n\n[messen]\nfahrt = true\n',
                    encoding="utf-8")
    assert profil.laden(pfad).fahrt_automatisch is True
