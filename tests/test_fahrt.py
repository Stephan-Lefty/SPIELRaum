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


def test_auswahl_der_varianten(tmp_path):
    """Nicht jede Variante muss in die Messfahrt.

    Vier Läufe sind drei Viertelstunden Spielzeit. Oft genügen die beiden
    Enden – und eine persönliche Lieblingseinstellung ist keine Richtung,
    die zur Auswahl steht.
    """
    from spielraum import profil
    pfad = tmp_path / "t.toml"
    pfad.write_text(
        '[spiel]\nname = "X"\n\n[messen]\nfahrt = true\n'
        'fahrt_varianten = ["optik", "leistung"]\n', encoding="utf-8")
    assert profil.laden(pfad).fahrt_varianten == ["optik", "leistung"]


def test_unbekannte_variante_in_der_auswahl_wird_gemeldet(tmp_path):
    """Ein Tippfehler darf nicht stillschweigend die ganze Auswahl kippen."""
    from spielraum import profil
    pfad = tmp_path / "t.toml"
    pfad.write_text(
        '[spiel]\nname = "X"\n\n[messen]\nfahrt_varianten = ["gibtsnicht"]\n'
        '\n[varianten.optik]\nbeschreibung = "hübsch"\n', encoding="utf-8")
    p = profil.laden(pfad)
    assert any("gibtsnicht" in w for w in p.warnungen())


def test_auswahl_muss_eine_liste_sein(tmp_path):
    from spielraum import profil
    pfad = tmp_path / "t.toml"
    pfad.write_text('[spiel]\nname = "X"\n\n[messen]\nfahrt_varianten = "optik"\n',
                    encoding="utf-8")
    with pytest.raises(profil.ProfilFehler):
        profil.laden(pfad)


# --- Welche Varianten gemessen werden --------------------------------------
#
# Der Fehler vom 05.11.2026: »messen.fahrt_varianten« galt nur für die Fahrt,
# die von selbst beginnt. Von Hand begonnen -- über die Kommandozeile oder die
# Oberfläche -- wurden stumm alle Varianten genommen. Im Profil standen zwei,
# angekündigt wurden vier Läufe zu je zehn Minuten: vierzig Minuten Spielzeit
# statt zwanzig. Deshalb hat jeder der drei Wege hier einen eigenen Test.


def _profil_mit_varianten(tmp_path, auswahl):
    from spielraum.profil import Profil, Variante

    p = Profil(name="Testspiel", quelle=tmp_path / "x.toml", steam_app_id=42)
    p.varianten = {n: Variante(n, n, {}) for n in
                   ("optik", "ausgeglichen", "leistung", "stephan")}
    p.fahrt_varianten = list(auswahl)
    return p


def test_profil_nennt_nur_die_gewaehlten(tmp_path):
    p = _profil_mit_varianten(tmp_path, ["optik", "leistung"])
    assert p.mess_varianten() == ["optik", "leistung"]


def test_ohne_auswahl_gelten_alle(tmp_path):
    p = _profil_mit_varianten(tmp_path, [])
    assert len(p.mess_varianten()) == 4


def test_tippfehler_verhindert_die_fahrt_nicht(tmp_path):
    """Ein unbekannter Name fällt heraus, er blockiert nicht.

    Bleibt nichts übrig, gelten alle – sonst stünde man vor einer Fahrt,
    die sich nicht beginnen lässt, und die Meldung dazu stünde woanders
    (in ``warnungen()``).
    """
    p = _profil_mit_varianten(tmp_path, ["optik", "gibtsnicht"])
    assert p.mess_varianten() == ["optik"]
    p = _profil_mit_varianten(tmp_path, ["nurquatsch"])
    assert len(p.mess_varianten()) == 4


def test_kommandozeile_beachtet_die_auswahl(tmp_path, monkeypatch, capsys):
    """Der Weg, auf dem der Fehler aufgefallen ist."""
    from spielraum import cli, profil as profil_modul

    p = _profil_mit_varianten(tmp_path, ["optik", "leistung"])
    monkeypatch.setattr(profil_modul, "finden", lambda **k: p)
    monkeypatch.setattr(cli.profil, "finden", lambda **k: p)

    cli.main(["messfahrt", "42", "--starten"])
    ausgabe = capsys.readouterr().out
    assert "2 Läufe" in ausgabe, ausgabe
    assert "ausgeglichen" not in ausgabe

    akte = fahrt.lesen(42)
    assert akte is not None and akte.varianten == ["optik", "leistung"]


def test_nur_sticht_die_profilauswahl(tmp_path, monkeypatch, capsys):
    """»--nur« gilt für diesen einen Aufruf, auch gegen das Profil."""
    from spielraum import cli, profil as profil_modul

    p = _profil_mit_varianten(tmp_path, ["optik", "leistung"])
    monkeypatch.setattr(profil_modul, "finden", lambda **k: p)
    monkeypatch.setattr(cli.profil, "finden", lambda **k: p)

    cli.main(["messfahrt", "42", "--starten", "--nur", "optik,stephan"])
    akte = fahrt.lesen(42)
    assert akte is not None and akte.varianten == ["optik", "stephan"]


# --- Mitläufer in der Messfahrt --------------------------------------------


def test_fahrt_meldet_weit_auseinanderliegende_cpu_last():
    """Zwei Rechnerzustände sind keine zwei Varianten.

    Nachgebaut mit den Werten vom 10. und 12.11.2026: 28,6 gegen 68,9
    Prozent CPU-Last, weil bei einem Lauf OBS mitschnitt.
    """
    f = fahrt.Fahrt(spiel="Test", steam_app_id=1, varianten=["optik", "leistung"])
    f.vermerken(fahrt.Lauf(variante="optik", messdatei="a.csv", mittel=49.4,
                           tief_1=22.2, dauer=5767.0, cpu_last=28.6))
    f.vermerken(fahrt.Lauf(variante="leistung", messdatei="b.csv", mittel=46.9,
                           tief_1=17.4, dauer=2218.0, cpu_last=68.9))

    hinweis = f.mitlaeufer_hinweis()
    assert hinweis is not None
    assert "40 Prozentpunkte" in hinweis
    assert "»leistung«" in hinweis  # der Lauf mit der höheren Last
    assert "wiederholen" in hinweis


def test_fahrt_ohne_auffaelligkeit_schweigt():
    f = fahrt.Fahrt(spiel="Test", steam_app_id=1, varianten=["optik", "leistung"])
    f.vermerken(fahrt.Lauf(variante="optik", messdatei="a.csv", mittel=44.5,
                           tief_1=23.5, dauer=2428.0, cpu_last=26.1))
    f.vermerken(fahrt.Lauf(variante="leistung", messdatei="b.csv", mittel=52.5,
                           tief_1=22.9, dauer=758.0, cpu_last=25.7))
    assert f.mitlaeufer_hinweis() is None


def test_fahrt_ohne_cpu_last_schweigt():
    """Akten aus Fassung 1 kennen die Spalte nicht.

    Ein stillschweigendes 0,0 darf nicht als »Prozessor im Leerlauf«
    gelesen werden und einen Verdacht erzeugen, der aus nichts kommt.
    """
    f = fahrt.Fahrt(spiel="Test", steam_app_id=1, varianten=["optik", "leistung"])
    f.vermerken(fahrt.Lauf(variante="optik", messdatei="a.csv", mittel=44.5,
                           tief_1=23.5, dauer=2428.0))
    f.vermerken(fahrt.Lauf(variante="leistung", messdatei="b.csv", mittel=52.5,
                           tief_1=22.9, dauer=758.0, cpu_last=68.9))
    assert f.mitlaeufer_hinweis() is None


def test_akte_aus_fassung_1_bleibt_lesbar(tmp_path, monkeypatch):
    """Sonst wäre eine fertig gemessene Fahrt verloren, weil eine Spalte
    dazugekommen ist. Dieselbe Entscheidung wie beim Zustandsjournal."""
    import json

    monkeypatch.setattr(fahrt.umgebung, "daten_verzeichnis", lambda: tmp_path)
    akte = {
        "spiel": "Road to Vostok", "steam_app_id": 1963610,
        "varianten": ["optik", "leistung"], "ausgangszustand": None,
        "angelegt": 1.0, "abgeschlossen": True, "uebernommen": "",
        "fassung": 1,
        "laeufe": [{"variante": "optik", "messdatei": "a.csv", "mittel": 44.5,
                    "tief_1": 23.5, "tief_01": 0.1, "dauer": 2428.0,
                    "verworfen": ""}],
    }
    fahrt.akte_pfad(1963610).write_text(json.dumps(akte), encoding="utf-8")

    gelesen = fahrt.lesen(1963610)
    assert gelesen is not None
    assert gelesen.laeufe[0].mittel == 44.5
    assert gelesen.laeufe[0].cpu_last == 0.0  # nicht mitgeschrieben
    assert gelesen.fassung == fahrt.FAHRT_FASSUNG  # wird fortgeschrieben


def test_akte_mit_unbekanntem_feld_stuerzt_nicht_ab(tmp_path, monkeypatch):
    """Eine Akte aus einer späteren Fassung soll nicht mitten im
    Spielstart einen TypeError auslösen."""
    import json

    monkeypatch.setattr(fahrt.umgebung, "daten_verzeichnis", lambda: tmp_path)
    akte = {
        "spiel": "Test", "steam_app_id": 7, "varianten": ["a"],
        "fassung": 2, "was_ganz_neues": 42,
        "laeufe": [{"variante": "a", "messdatei": "x.csv", "mittel": 1.0,
                    "kommt_erst_spaeter": True}],
    }
    fahrt.akte_pfad(7).write_text(json.dumps(akte), encoding="utf-8")

    gelesen = fahrt.lesen(7)
    assert gelesen is not None
    assert gelesen.laeufe[0].mittel == 1.0
