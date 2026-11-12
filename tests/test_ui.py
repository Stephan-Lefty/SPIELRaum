"""Prüft die Oberfläche – auch dort, wo es sie gar nicht gibt.

Der wichtigste Test ist ``test_kern_braucht_keine_oberflaeche``. Er steht
hier, weil die Trennung sonst schleichend verlorengeht: Ein ``import`` an
der falschen Stelle, und die Kommandozeile startet auf einem Server nicht
mehr, auf dem nie jemand PySide6 installieren wollte.
"""

import importlib
import subprocess
import sys

import pytest


def test_kern_braucht_keine_oberflaeche():
    """Kein Modul des Kerns darf PySide6 hereinziehen.

    Geprüft in einem eigenen Prozess, in dem der Import von PySide6
    gesperrt ist – im laufenden Testprozess wäre es womöglich längst
    geladen und der Test grün, ohne etwas zu beweisen.
    """
    programm = (
        "import sys\n"
        "class Sperre:\n"
        "    def find_module(self, name, pfad=None):\n"
        "        if name.split('.')[0] == 'PySide6':\n"
        "            raise ImportError('PySide6 ist hier gesperrt')\n"
        "sys.meta_path.insert(0, Sperre())\n"
        "from spielraum import cli, profil, steam, messen, zustand, "
        "stellschrauben, umgebung, godot_cfg, starten\n"
        "cli.main(['umgebung'])\n"
        "print('OK')\n"
    )
    lauf = subprocess.run([sys.executable, "-c", programm],
                          capture_output=True, text=True)
    assert lauf.returncode == 0, lauf.stderr
    assert "OK" in lauf.stdout


def test_meldung_wenn_pyside_fehlt(monkeypatch):
    """Fehlt PySide6, soll der Installationsbefehl dastehen – nicht ein
    nackter ImportError."""
    from spielraum import ui

    echt = importlib.import_module

    def ohne_pyside(name, *args, **kwargs):
        if name.split(".")[0] == "PySide6":
            raise ImportError("gesperrt")
        return echt(name, *args, **kwargs)

    monkeypatch.setattr(importlib, "import_module", ohne_pyside)
    monkeypatch.setitem(sys.modules, "PySide6", None)
    sys.modules.pop("PySide6", None)

    import builtins
    echter_import = builtins.__import__

    def sperre(name, *args, **kwargs):
        if name.split(".")[0] == "PySide6":
            raise ImportError("gesperrt")
        return echter_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", sperre)

    ok, meldung = ui.verfuegbar()
    assert ok is False
    assert "pacman" in meldung or "apt" in meldung or "PySide6" in meldung


# Ab hier nur, wenn PySide6 tatsächlich da ist.
pyside = pytest.importorskip("PySide6", reason="PySide6 nicht installiert")


@pytest.fixture(scope="module")
def anwendung():
    """Eine QApplication ohne Bildschirm.

    ``offscreen`` ist der Grund, warum diese Tests auch in der CI laufen
    können, wo es keinen Grafikserver gibt.
    """
    import os
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    vorhanden = QApplication.instance()
    yield vorhanden or QApplication([])


def test_fenster_baut_sich(anwendung):
    from spielraum.ui.fenster import Fenster

    f = Fenster()
    assert "SPIELRaum" in f.windowTitle()
    # Die Liste kann leer sein - auf einem Rechner ohne Steam ist das der
    # Normalfall und kein Fehler.
    assert f.liste.count() == len(f.spiele) or f.liste.count() >= 0


def test_bericht_ohne_profil_und_ohne_messung(anwendung, tmp_path):
    """Ein Spiel ohne alles darf keinen leeren Kasten erzeugen."""
    from spielraum import steam
    from spielraum.ui.fenster import Fenster

    f = Fenster()
    erfunden = steam.Spiel(
        app_id=999999, name="Testspiel", ordner=tmp_path,
        groesse=1234567890, bibliothek=tmp_path,
    )
    html = f._bericht(erfunden)
    assert "Testspiel" in html
    assert "kein Profil" in html
    assert "Noch nichts gemessen" in html


def test_bericht_warnt_vor_drehender_platte(anwendung, tmp_path, monkeypatch):
    from spielraum import steam, umgebung
    from spielraum.ui.fenster import Fenster

    monkeypatch.setattr(umgebung, "platte_dreht", lambda p: True)
    f = Fenster()
    erfunden = steam.Spiel(
        app_id=999998, name="Auf Platte", ordner=tmp_path,
        groesse=5_600_000_000, bibliothek=tmp_path,
    )
    html = f._bericht(erfunden)
    assert "drehende Platte" in html
    assert "Engpass" in html


def _spiel_mit_loader(tmp_path, fassung="3.2.1"):
    """Ein erfundenes Spiel samt modloader.gd und Profil."""
    from spielraum import modloader, profil, steam

    ordner = tmp_path / "spiel"
    ordner.mkdir(exist_ok=True)
    kopf = f'const MODLOADER_VERSION := "{fassung}"\n'
    (ordner / "modloader.gd").write_text(
        kopf + "# Füllung\n" * (modloader.MINDESTGROESSE // 11), encoding="utf-8")

    p = profil.Profil(name="Loaderspiel", quelle=tmp_path / "x.toml",
                      steam_app_id=999001)
    p.modloader = "vostok"
    spiel = steam.Spiel(app_id=999001, name="Loaderspiel", ordner=ordner,
                        groesse=1, bibliothek=tmp_path)
    return p, spiel


def test_befund_zeigt_die_eingebaute_fassung(anwendung, tmp_path, monkeypatch):
    from spielraum import umgebung
    from spielraum.ui.fenster import Fenster

    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "daten"))
    umgebung.ermitteln.cache_clear()
    p, spiel = _spiel_mit_loader(tmp_path)

    html = "".join(Fenster()._modloader_abschnitt(p, spiel))
    assert "Mod Loader" in html
    assert "3.2.1" in html


def test_befund_behauptet_nicht_aktuell(anwendung, tmp_path, monkeypatch):
    """Ohne etwas im Zwischenlager darf dort nicht »aktuell« stehen.

    Geprüft wird beim Spielstart. Wer drei Wochen nicht gespielt hat, hat
    drei Wochen nicht geprüft – eine Oberfläche, die hier »aktuell« schreibt,
    sagt etwas, das sie nicht weiß. Dieselbe Haltung wie bei den Messungen.
    """
    from spielraum import umgebung
    from spielraum.ui.fenster import Fenster

    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "daten"))
    umgebung.ermitteln.cache_clear()
    p, spiel = _spiel_mit_loader(tmp_path)

    html = "".join(Fenster()._modloader_abschnitt(p, spiel))
    assert "aktuell" not in html.lower()
    assert "Nichts Neueres" in html


def test_knopf_erst_wenn_etwas_bereitliegt(anwendung, tmp_path, monkeypatch):
    """Ein Knopf, der meistens nichts tut, ist schlimmer als keiner."""
    from unittest import mock

    from spielraum import modloader, umgebung
    from spielraum.ui.fenster import Fenster

    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "daten"))
    umgebung.ermitteln.cache_clear()
    p, spiel = _spiel_mit_loader(tmp_path)
    quelle = modloader.QUELLEN["vostok"]

    _, stand = Fenster()._modloader_lage(p, spiel)
    assert stand.veraltet is False, "ohne Zwischenlager gibt es nichts zu tun"

    # Jetzt liegt eine neuere Fassung bereit.
    neuer = ('const MODLOADER_VERSION := "3.4.2"\n'
             + "# Füllung\n" * (modloader.MINDESTGROESSE // 11))
    with mock.patch.object(modloader, "_holen", return_value=neuer.encode()):
        modloader.herunterladen(quelle, "3.4.2")

    _, stand = Fenster()._modloader_lage(p, spiel)
    assert stand.veraltet is True
    assert stand.bereit is not None
    html = "".join(Fenster()._modloader_abschnitt(p, spiel))
    assert "3.4.2 liegt bereit" in html


def test_befund_fragt_nicht_im_netz(anwendung, tmp_path, monkeypatch):
    """Der wichtigste Test an diesem Abschnitt.

    Eine Netzabfrage beim Zeichnen friert das Fenster ein, bis die Antwort
    da ist – und bei einer abgelehnten Verbindung bis zur Zeitgrenze. Der
    Test fixiert nicht das Ergebnis, sondern dass gar nicht erst gefragt
    wird.
    """
    from unittest import mock

    from spielraum import modloader, umgebung
    from spielraum.ui.fenster import Fenster

    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "daten"))
    umgebung.ermitteln.cache_clear()
    p, spiel = _spiel_mit_loader(tmp_path)

    with mock.patch.object(modloader, "_holen",
                           side_effect=AssertionError("hat ins Netz gegriffen")):
        f = Fenster()
        f._modloader_abschnitt(p, spiel)
        f._modloader_lage(p, spiel)


def test_ohne_loader_im_profil_kein_abschnitt(anwendung, tmp_path):
    from spielraum.ui.fenster import Fenster

    p, spiel = _spiel_mit_loader(tmp_path)
    p.modloader = ""
    assert Fenster()._modloader_abschnitt(p, spiel) == []


def test_tastenblatt_wird_gefunden(tmp_path, monkeypatch):
    """Das eigene Blatt zum Spiel, gesucht über den Spielnamen.

    Über den Namen und nicht über die App-ID, weil die Dateien zum Lesen
    gedacht sind: »Road-to-Vostok-Tastenbelegung.pdf« findet man im
    Dateiverwalter wieder, »1963610.pdf« nicht.
    """
    from spielraum import steam
    from spielraum.ui import fenster

    ordner = tmp_path / "tastenblaetter"
    ordner.mkdir()
    (ordner / "Road-to-Vostok-Tastenbelegung.pdf").write_bytes(b"%PDF-1.4\n")

    # Der Ordner wird relativ zum Modul gesucht – hier umbiegen.
    monkeypatch.setattr(fenster, "__file__", str(tmp_path / "x" / "y" / "z.py"))

    spiel = steam.Spiel(app_id=1963610, name="Road to Vostok", ordner=tmp_path,
                        groesse=1, bibliothek=tmp_path)
    assert fenster._tastenblatt(spiel) is not None


def test_ohne_tastenblatt_kein_verweis(tmp_path, monkeypatch):
    """Kein Blatt, kein Link. Ein Verweis ins Leere ist schlimmer als keiner."""
    from spielraum import steam
    from spielraum.ui import fenster

    monkeypatch.setattr(fenster, "__file__", str(tmp_path / "x" / "y" / "z.py"))
    spiel = steam.Spiel(app_id=999997, name="Gibt Es Nicht", ordner=tmp_path,
                        groesse=1, bibliothek=tmp_path)
    assert fenster._tastenblatt(spiel) is None


def test_messfahrt_knopf_beachtet_die_profilauswahl(anwendung, tmp_path, monkeypatch):
    """Der dritte Weg in eine Messfahrt – und der, auf dem es niemand sah.

    Am 05.11.2026 nahmen Kommandozeile und Oberfläche stur alle Varianten,
    während »messen.fahrt_varianten« nur für die automatisch begonnene Fahrt
    galt. Aus zwei angekündigten Läufen wurden vier, also vierzig Minuten
    Spielzeit statt zwanzig.
    """
    from PySide6.QtWidgets import QMessageBox

    from spielraum import fahrt, steam
    from spielraum.profil import Profil, Variante
    from spielraum.ui import fenster as fenster_modul
    from spielraum.ui.fenster import Fenster

    monkeypatch.setattr(fahrt.umgebung, "daten_verzeichnis", lambda: tmp_path)

    p = Profil(name="Testspiel", quelle=tmp_path / "x.toml", steam_app_id=4242)
    p.varianten = {n: Variante(n, n, {}) for n in
                   ("optik", "ausgeglichen", "leistung", "stephan")}
    p.fahrt_varianten = ["optik", "leistung"]
    monkeypatch.setattr(fenster_modul.profil, "finden", lambda **k: p)

    gezeigt = []
    monkeypatch.setattr(QMessageBox, "question",
                        lambda *a, **k: (gezeigt.append(a[2]), QMessageBox.Yes)[1])
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None)

    f = Fenster()
    f.spiele = [steam.Spiel(app_id=4242, name="Testspiel", ordner=tmp_path,
                            groesse=1, bibliothek=tmp_path)]
    monkeypatch.setattr(f.liste, "currentRow", lambda: 0)
    f._messfahrt()

    akte = fahrt.lesen(4242)
    assert akte is not None, "es wurde keine Fahrt angelegt"
    assert akte.varianten == ["optik", "leistung"]
    assert "2 Läufe" in gezeigt[0], gezeigt[0]
    assert "ausgeglichen" not in gezeigt[0]


def test_tastenblatt_wird_nicht_im_befund_geoeffnet(anwendung, tmp_path, monkeypatch):
    """Der Fehler vom 05.11.2026.

    Ein Klick auf »Tastenblatt öffnen« lud die PDF **in den Befund** – dort
    stand dann »%PDF-1.4 ReportLab Generated PDF document« als Rohtext.
    ``setOpenExternalLinks(True)`` genügt nicht: Ein QTextBrowser hält eine
    ``file://``-Adresse für ein Dokument, das er selbst anzeigen kann.

    Der Test fixiert nicht das Aussehen, sondern die Abstinenz: Das Feld
    darf Verweisen gar nicht erst folgen.
    """
    from spielraum.ui.fenster import Fenster

    f = Fenster()
    assert f.befund.openLinks() is False, \
        "der Befund folgt Verweisen selbst – dann landet die PDF in ihm"


def test_tastenblatt_adresse_vertraegt_leerzeichen(anwendung, tmp_path, monkeypatch):
    """Der Pfad zu diesem Repository enthält ein Leerzeichen.

    »/mnt/raid/eigene Daten/…« – unkodiert ist das keine gültige Adresse,
    und der Klick ginge ins Leere. Beim Zusammensetzen von Hand fällt so
    etwas erst auf dem Rechner auf, auf dem der Pfad anders aussieht.
    """
    from spielraum import steam
    from spielraum.ui import fenster as fenster_modul
    from spielraum.ui.fenster import Fenster

    ordner = tmp_path / "mit Leerzeichen" / "tastenblaetter"
    ordner.mkdir(parents=True)
    (ordner / "Road-to-Vostok-Tastenbelegung.pdf").write_bytes(b"%PDF-1.4\n")
    monkeypatch.setattr(
        fenster_modul, "__file__",
        str(tmp_path / "mit Leerzeichen" / "x" / "y" / "z.py"))

    p = profil_fuer_tasten(tmp_path)
    monkeypatch.setattr(fenster_modul.profil, "finden", lambda **k: p)
    spiel = steam.Spiel(app_id=1963610, name="Road to Vostok", ordner=tmp_path,
                        groesse=1, bibliothek=tmp_path)

    html = Fenster()._bericht(spiel)
    assert "Tastenblatt öffnen" in html, "der Verweis fehlt ganz"
    assert "mit Leerzeichen" not in html or "%20" in html, \
        "das Leerzeichen steht unkodiert in der Adresse"


def profil_fuer_tasten(tmp_path):
    from spielraum.profil import Profil

    p = Profil(name="Road to Vostok", quelle=tmp_path / "x.toml",
               steam_app_id=1963610)
    p.tasten = {"insert": "r"}
    return p


def test_klick_auf_bereits_gewaehltes_spiel_liest_neu(anwendung, tmp_path, monkeypatch):
    """Der Fehler vom 09.11.2026.

    ``currentRowChanged`` feuert nur bei einem Zeilenwechsel. Wer auf das
    ohnehin ausgewählte Spiel klickt, um den Befund aufzufrischen, bekam
    nichts – der Mod-Loader-Knopf blieb grau, obwohl eine neuere Fassung
    bereitlag. Erst »Neu einlesen« half, weil das Leeren der Liste einen
    Zeilenwechsel erzwingt.

    Geprüft wird die Verdrahtung, nicht das Ergebnis: Ein Klick auf einen
    Eintrag muss ``_gewaehlt`` erreichen, auch wenn die Zeile dieselbe
    bleibt.
    """
    from PySide6.QtWidgets import QListWidgetItem

    from spielraum.ui.fenster import Fenster

    f = Fenster()
    f.liste.clear()
    f.liste.addItem(QListWidgetItem("Testspiel"))
    f.liste.setCurrentRow(0)

    gerufen = []
    monkeypatch.setattr(f, "_gewaehlt", lambda z: gerufen.append(z))

    # Zeile bleibt 0 – ohne die itemClicked-Verbindung passiert hier nichts.
    f.liste.itemClicked.emit(f.liste.item(0))
    assert gerufen == [0], "ein Klick auf das gewählte Spiel liest nicht neu"


# --- Der Knopf zu den Aufnahmen --------------------------------------------


def test_aufnahmeknopf_bleibt_grau_ohne_bilder(anwendung, tmp_path, monkeypatch):
    """Ein Knopf, der ein leeres Fenster öffnet, ist schlimmer als ein grauer.

    Steam legt den Screenshot-Ordner schon beim ersten Spielstart an --
    »Ordner vorhanden« ist deshalb kein Grund, den Knopf freizugeben.
    """
    from spielraum import steam
    from spielraum.ui import fenster as fenster_modul
    from spielraum.ui.fenster import Fenster

    spiel = steam.Spiel(app_id=1203620, name="Enshrouded", ordner=tmp_path,
                        groesse=1, bibliothek=tmp_path)
    monkeypatch.setattr(fenster_modul.steam, "bilder_zaehlen", lambda app: 0)
    monkeypatch.setattr(fenster_modul.profil, "finden", lambda **k: None)

    f = Fenster()
    f.spiele = [spiel]
    f._gewaehlt(0)
    assert f.knopf_bilder.isEnabled() is False
    assert f.knopf_bilder.text() == "Aufnahmen"


def test_aufnahmeknopf_nennt_die_anzahl(anwendung, tmp_path, monkeypatch):
    """Die Zahl steht auf dem Knopf, damit man vor dem Klick weiß, was kommt."""
    from spielraum import steam
    from spielraum.ui import fenster as fenster_modul
    from spielraum.ui.fenster import Fenster

    spiel = steam.Spiel(app_id=1963610, name="Road to Vostok", ordner=tmp_path,
                        groesse=1, bibliothek=tmp_path)
    monkeypatch.setattr(fenster_modul.steam, "bilder_zaehlen", lambda app: 13)
    monkeypatch.setattr(fenster_modul.profil, "finden", lambda **k: None)

    f = Fenster()
    f.spiele = [spiel]
    f._gewaehlt(0)
    assert f.knopf_bilder.isEnabled() is True
    assert "13" in f.knopf_bilder.text()


def test_aufnahmeknopf_oeffnet_den_ordner_nicht_im_befund(anwendung, tmp_path,
                                                          monkeypatch):
    """Dieselbe Falle wie beim Tastenblatt am 05.11.2026: Der Ordner gehört
    in den Dateiverwalter, nicht in ein Textfeld.

    Geprüft wird die Adresse, die SPIELRaum dem Schreibtisch übergibt --
    und dass sie ein Leerzeichen im Pfad verträgt.
    """
    from spielraum import steam
    from spielraum.ui import fenster as fenster_modul
    from spielraum.ui.fenster import Fenster

    ordner = tmp_path / "mit Leerzeichen" / "screenshots"
    ordner.mkdir(parents=True)
    gerufen = []
    monkeypatch.setattr(fenster_modul.steam, "bilder_zaehlen", lambda app: 2)
    monkeypatch.setattr(fenster_modul.steam, "bilderordner", lambda app: [ordner])
    monkeypatch.setattr(fenster_modul.QDesktopServices, "openUrl",
                        lambda url: gerufen.append(url.toString()))
    monkeypatch.setattr(fenster_modul.profil, "finden", lambda **k: None)

    f = Fenster()
    f.spiele = [steam.Spiel(app_id=1963610, name="Road to Vostok",
                            ordner=tmp_path, groesse=1, bibliothek=tmp_path)]
    f.liste.addItem("Road to Vostok")
    f.liste.setCurrentRow(0)
    f._bilder_oeffnen()

    assert len(gerufen) == 1, "der Ordner wurde nicht geöffnet"
    assert gerufen[0].startswith("file://")
    assert "mit%20Leerzeichen" in gerufen[0] or "mit Leerzeichen" in gerufen[0]


# --- Die Mitläufer-Warnung in der Befundtafel ------------------------------

KOPF_CSV = (
    "os,cpu,gpu,ram,kernel,driver,cpuscheduler\n"
    "Test Linux,Test-Prozessor,Test-Grafik,32800000,6.0.0-test,,powersave\n"
    "fps,frametime,cpu_load,gpu_load,elapsed\n"
)


def _messlauf_schreiben(ordner, name, fps, cpu, stichproben=6000):
    """Ein Protokoll von zehn Minuten – über der Mindestzeit."""
    ordner.mkdir(parents=True, exist_ok=True)
    zeilen = [KOPF_CSV]
    for n in range(1, stichproben + 1):
        zeilen.append(f"{fps},16.0,{cpu},50.0,{n * 100_000_000}\n")
    (ordner / f"{name}.csv").write_text("".join(zeilen), encoding="utf-8")


def _befund_fuer(tmp_path, monkeypatch, laeufe):
    from spielraum import steam
    from spielraum.ui import fenster as fenster_modul
    from spielraum.ui.fenster import Fenster
    import re

    messordner = tmp_path / "messungen"
    for name, fps, cpu in laeufe:
        _messlauf_schreiben(messordner / "4242", name, fps, cpu)
    monkeypatch.setattr(fenster_modul.stellschrauben, "messordner",
                        lambda: messordner)
    monkeypatch.setattr(fenster_modul.profil, "finden", lambda **k: None)
    monkeypatch.setattr(fenster_modul.steam, "bilder_zaehlen", lambda app: 0)

    spiel = steam.Spiel(app_id=4242, name="Testspiel", ordner=tmp_path,
                        groesse=1, bibliothek=tmp_path)
    html = Fenster()._bericht(spiel)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


def test_befund_warnt_wenn_der_juengste_lauf_auffaellt(anwendung, tmp_path,
                                                       monkeypatch):
    """Der Fall vom 12.11.2026: Beim letzten Lauf schnitt OBS mit."""
    text = _befund_fuer(tmp_path, monkeypatch, [
        ("a_2026-11-10_10-00-00", 49.4, 25.0),
        ("b_2026-11-12_10-00-00", 46.9, 59.0),
    ])
    assert "CPU-Last unterscheidet sich" in text
    assert "34 Prozentpunkte" in text


def test_befund_warnt_nicht_wegen_eines_alten_laufs(anwendung, tmp_path,
                                                    monkeypatch):
    """Der Fehlalarm vom 12.11.2026, gefunden beim Durchtesten.

    Die erste Fassung nahm Höchst gegen Tiefst über sechs Läufe. Bei
    Enshrouded liegen die sauberen Läufe von 39 bis 53 Prozent auseinander
    -- also schlug die Warnung dort immer an. Eine Warnung, die immer kommt,
    liest nach der dritten niemand mehr.

    Gewarnt wird deshalb über die beiden jüngsten Läufe, wie auf der
    Kommandozeile. Der auffällige alte Lauf steht weiter in der Tabelle.
    """
    text = _befund_fuer(tmp_path, monkeypatch, [
        ("a_2026-11-06_10-00-00", 48.8, 82.0),   # der auffällige, aber alt
        ("b_2026-11-10_10-00-00", 27.5, 49.8),
        ("c_2026-11-10_11-00-00", 23.6, 53.0),   # die beiden jüngsten:
    ])                                           # 3,2 Punkte Unterschied
    assert "CPU-Last unterscheidet sich" not in text
    assert "82" in text, "der auffällige Lauf soll in der Tabelle stehen"


# --- Die Stelle der Anzeige umschalten -------------------------------------


def _profil_datei(ordner, app_id=4242, ecke=None):
    inhalt = f'[spiel]\nname = "Testspiel"\nsteam_app_id = {app_id}\n\n'
    inhalt += "# Ein Kommentar, der überleben muss.\n[messen]\nmangohud = true\n"
    if ecke:
        inhalt += f'ecke = "{ecke}"  # mit Kommentar am Zeilenende\n'
    datei = ordner / f"{app_id}-test.toml"
    datei.write_text(inhalt, encoding="utf-8")
    return datei


def _fenster_mit_profil(tmp_path, monkeypatch, ecke=None):
    from spielraum import profil as profil_modul
    from spielraum import steam
    from spielraum.ui import fenster as fenster_modul
    from spielraum.ui.fenster import Fenster

    verzeichnis = tmp_path / "spiele"
    verzeichnis.mkdir()
    datei = _profil_datei(verzeichnis, ecke=ecke)
    monkeypatch.setattr(profil_modul, "profil_verzeichnis", lambda: verzeichnis)
    monkeypatch.setattr(fenster_modul.steam, "bilder_zaehlen", lambda app: 0)

    spiel = steam.Spiel(app_id=4242, name="Testspiel", ordner=tmp_path,
                        groesse=1, bibliothek=tmp_path)
    f = Fenster()
    f.spiele = [spiel]
    f.liste.clear()
    f.liste.addItem("Testspiel")
    f.liste.setCurrentRow(0)
    f._gewaehlt(0)
    return f, datei


def test_spielwechsel_schreibt_nicht_ins_profil(anwendung, tmp_path, monkeypatch):
    """Die gefährliche Stelle.

    ``currentIndexChanged`` feuert auch, wenn das Feld BEFÜLLT wird. Ohne
    Sperre schreibt jeder Blick auf ein Spiel in dessen Profildatei --
    dieselbe Falle wie bei ``currentRowChanged`` am 09.11.2026, nur in die
    andere Richtung.
    """
    f, datei = _fenster_mit_profil(tmp_path, monkeypatch, ecke="bottom-right")
    vorher = datei.read_bytes()

    for _ in range(3):
        f._gewaehlt(0)   # mehrfach wählen, wie beim Hin- und Herklicken

    assert datei.read_bytes() == vorher, "das Profil wurde ungefragt geändert"
    assert f.anzeige_ecke.currentData() == "bottom-right"


def test_auswahl_schreibt_die_stelle_ins_profil(anwendung, tmp_path, monkeypatch):
    from spielraum import profil as profil_modul

    f, datei = _fenster_mit_profil(tmp_path, monkeypatch, ecke="top-left")
    zeile = f.anzeige_ecke.findData("middle-right")
    f.anzeige_ecke.setCurrentIndex(zeile)

    assert profil_modul.laden(datei).overlay_ecke == "middle-right"
    assert "Ein Kommentar, der überleben muss." in datei.read_text(encoding="utf-8")
    assert "mit Kommentar am Zeilenende" in datei.read_text(encoding="utf-8"), \
        "der Kommentar hinter dem Wert ist verschwunden"
    assert "Mitte rechts" in f.unterzeile.text()
    assert "nächsten Start" in f.unterzeile.text(), \
        "es muss dastehen, dass es erst beim nächsten Start wirkt"


def test_ohne_ecke_im_profil_wird_sie_angelegt(anwendung, tmp_path, monkeypatch):
    from spielraum import profil as profil_modul

    f, datei = _fenster_mit_profil(tmp_path, monkeypatch, ecke=None)
    assert f.anzeige_ecke.currentData() == "top-left", "die Vorgabe soll stehen"

    f.anzeige_ecke.setCurrentIndex(f.anzeige_ecke.findData("bottom-left"))
    assert profil_modul.laden(datei).overlay_ecke == "bottom-left"
    assert "mangohud = true" in datei.read_text(encoding="utf-8")


def test_ohne_profil_bleibt_das_feld_grau(anwendung, tmp_path, monkeypatch):
    from spielraum import steam
    from spielraum.ui import fenster as fenster_modul
    from spielraum.ui.fenster import Fenster

    monkeypatch.setattr(fenster_modul.profil, "finden", lambda **k: None)
    monkeypatch.setattr(fenster_modul.steam, "bilder_zaehlen", lambda app: 0)
    spiel = steam.Spiel(app_id=99, name="Ohne Profil", ordner=tmp_path,
                        groesse=1, bibliothek=tmp_path)
    f = Fenster()
    f.spiele = [spiel]
    f.liste.clear(); f.liste.addItem("Ohne Profil"); f.liste.setCurrentRow(0)
    f._gewaehlt(0)
    assert f.anzeige_ecke.isEnabled() is False
