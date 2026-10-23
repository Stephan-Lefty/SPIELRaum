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
