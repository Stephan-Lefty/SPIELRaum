"""Prüft die Tastenbelegung – vor allem dort, wo sie Nein sagen muss.

keyd wird hier nirgends wirklich aufgerufen. Die Tests ersetzen die Liste
der gültigen Tasten und den Unterprozessaufruf: Ein Test, der den echten
Dienst braucht, läuft weder in der CI noch auf einem Rechner ohne keyd.
"""

from unittest import mock

import pytest

from spielraum import profil, tasten
from spielraum.zustand import Journal

# Was ein gedachtes keyd als gültig ausgibt -- bewusst klein gehalten.
GUELTIG = frozenset({"up", "down", "left", "right", "pageup", "pagedown",
                     "end", "home", "insert", "delete", "w", "a", "s", "d",
                     "e", "r", "b", "space", "tab", "leftshift", "leftcontrol"})


@pytest.fixture(autouse=True)
def _tastenliste():
    """Die Abfrage bei keyd durch eine feste Liste ersetzen."""
    tasten.bekannte_tasten.cache_clear()
    with mock.patch.object(tasten, "bekannte_tasten", return_value=GUELTIG):
        yield
    tasten.bekannte_tasten.cache_clear()


# --- Prüfung ---------------------------------------------------------------


def test_gueltige_belegung_wird_durchgelassen():
    assert tasten.pruefen({"up": "w", "pageup": "space"}) == []


def test_ebenen_sind_erlaubt():
    """``layer(shift)`` muss durch, sonst verhält sich Umschalt falsch.

    Steht rechts nur ``leftshift``, schickt keyd den Tastencode, führt ihn
    aber nicht als Modifikator. Beim Sprinten hält man die Taste und bewegt
    sich gleichzeitig -- das muss zusammengehen.
    """
    assert tasten.pruefen({"pagedown": "layer(shift)"}) == []


def test_erfundene_ebene_wird_abgelehnt():
    beanstandet = tasten.pruefen({"up": "layer(quatsch)"})
    assert len(beanstandet) == 1
    assert "quatsch" in beanstandet[0]


def test_tippfehler_wird_benannt():
    """Die Meldung muss sagen *welche* Taste falsch ist, nicht nur »ungültig«."""
    beanstandet = tasten.pruefen({"upp": "w"})
    assert beanstandet == ["»upp« ist keine Taste, die keyd kennt"]


def test_befehl_im_profil_wird_abgelehnt():
    """Der Fall, gegen den die Prüfung überhaupt gebaut ist.

    Ein Profil ist eine Datei, die jeder bearbeiten kann. Was daraus in
    einen Aufruf wandert, läuft gegen eine feste Liste -- siehe die
    Sicherheitsregel in CLAUDE.md.
    """
    assert tasten.pruefen({"up": "; rm -rf /"}) != []
    assert tasten.pruefen({"$(whoami)": "w"}) != []


def test_ohne_keyd_wird_nicht_beanstandet():
    """Fehlt keyd, lässt sich nichts prüfen – also auch nichts bemängeln.

    Das Nein kommt dann aus ``verfuegbar()``, nicht aus der Prüfung. Sonst
    bekäme jemand ohne keyd eine Liste erfundener Fehler zu lesen.
    """
    with mock.patch.object(tasten, "bekannte_tasten", return_value=frozenset()):
        assert tasten.pruefen({"up": "w"}) == []


# --- Setzen ----------------------------------------------------------------


def test_leere_belegung_tut_nichts():
    journal = Journal(spiel="Test", pid=1)
    assert tasten.setzen({}, journal) == []
    assert journal.eintraege == []


def test_ungueltige_belegung_bricht_ab_bevor_etwas_passiert():
    """Erst prüfen, dann journalisieren, dann setzen – in dieser Reihenfolge.

    Stünde der Journaleintrag vor der Prüfung, bliebe nach einem Tippfehler
    ein Eintrag liegen, zu dem es nie eine Änderung gab.
    """
    journal = Journal(spiel="Test", pid=1)
    with pytest.raises(tasten.TastenFehler) as fehler:
        tasten.setzen({"upp": "w"}, journal)
    assert "upp" in str(fehler.value)
    assert journal.eintraege == []


def test_journal_entsteht_vor_dem_aufruf():
    """Der Eintrag muss liegen, bevor keyd etwas tut.

    Bricht SPIELRaum dazwischen ab, findet der nächste Start den Eintrag
    und setzt zurück. Andersherum bliebe eine Tastatur zurück, die bis zum
    Neustart falsch schreibt.
    """
    journal = Journal(spiel="Test", pid=1)
    reihenfolge = []

    def vermerken(*args, **kwargs):
        reihenfolge.append("journal")
        return Journal.vermerken(journal, *args, **kwargs)

    def aufruf(*args, **kwargs):
        reihenfolge.append("keyd")
        return mock.Mock(returncode=0, stdout="", stderr="")

    with mock.patch.object(tasten, "verfuegbar", return_value=(True, "")), \
         mock.patch.object(journal, "vermerken", side_effect=vermerken), \
         mock.patch.object(tasten.subprocess, "run", side_effect=aufruf):
        tasten.setzen({"up": "w"}, journal)

    assert reihenfolge == ["journal", "keyd"]


def test_fehlende_gruppe_erklaert_den_weg():
    """Die Meldung muss den Befehl nennen, nicht nur das Problem."""
    journal = Journal(spiel="Test", pid=1)
    with mock.patch.object(
        tasten, "verfuegbar",
        return_value=(False, "Kein Zugriff auf /run/keyd.socket. Einmalig "
                             "einrichten mit: sudo usermod -aG keyd $USER"),
    ), pytest.raises(tasten.TastenFehler) as fehler:
        tasten.setzen({"up": "w"}, journal)
    assert "usermod" in str(fehler.value)


def test_keyd_lehnt_ab_wird_weitergereicht():
    journal = Journal(spiel="Test", pid=1)
    with mock.patch.object(tasten, "verfuegbar", return_value=(True, "")), \
         mock.patch.object(tasten.subprocess, "run",
                           return_value=mock.Mock(returncode=1, stdout="",
                                                  stderr="so nicht")), \
         pytest.raises(tasten.TastenFehler) as fehler:
        tasten.setzen({"up": "w"}, journal)
    assert "so nicht" in str(fehler.value)


# --- Rechteprüfung ---------------------------------------------------------


def test_pruefung_ruft_keyd_ueberhaupt_nicht_auf(tmp_path):
    """Der Kern des Fehlers vom 03.11.2026.

    Hier stand ``keyd bind reset`` als Testaufruf – derselbe Befehl, mit dem
    ``zuruecknehmen()`` alles verwirft. Weil der Befund im Fenster diese
    Prüfung bei jedem Spielwechsel aufruft, löschte ein Klick in die
    Spieleliste die laufende Belegung.

    Der Test fixiert nicht das Ergebnis, sondern die Abwesenheit des
    Aufrufs: Egal wie die Prüfung künftig aussieht, sie darf keinen
    Unterprozess starten.
    """
    socket = tmp_path / "keyd.socket"
    socket.touch()
    with mock.patch.object(tasten, "SOCKETS", (str(socket),)), \
         mock.patch.object(tasten.subprocess, "run") as lauf:
        erreichbar, _ = tasten._socket_erreichbar()
    assert erreichbar is True
    lauf.assert_not_called()


def test_ohne_schreibrecht_nennt_den_befehl(tmp_path):
    """Kein Zugriff ist kein Absturz, sondern eine Anleitung."""
    socket = tmp_path / "keyd.socket"
    socket.touch()
    with mock.patch.object(tasten, "SOCKETS", (str(socket),)), \
         mock.patch.object(tasten.os, "access", return_value=False):
        erreichbar, grund = tasten._socket_erreichbar()
    assert erreichbar is False
    assert "usermod -aG keyd" in grund


def test_fehlender_socket_sagt_wo_gesucht_wurde(tmp_path):
    """Ein pauschales Nein hilft niemandem weiter."""
    with mock.patch.object(tasten, "SOCKETS", (str(tmp_path / "gibtsnicht"),)):
        erreichbar, grund = tasten._socket_erreichbar()
    assert erreichbar is False
    assert "gibtsnicht" in grund


# --- Zurücknehmen ----------------------------------------------------------


def test_zuruecknehmen_ohne_keyd_meldet_sachlich():
    with mock.patch.object(tasten.umgebung, "ermitteln") as ermitteln:
        ermitteln.return_value.pfad.return_value = None
        assert "nicht installiert" in tasten.zuruecknehmen()


def test_zuruecknehmen_ruft_reset():
    with mock.patch.object(tasten.umgebung, "ermitteln") as ermitteln, \
         mock.patch.object(tasten.subprocess, "run") as lauf:
        ermitteln.return_value.pfad.return_value = "/usr/bin/keyd"
        lauf.return_value = mock.Mock(returncode=0, stdout="", stderr="")
        tasten.zuruecknehmen()
    assert lauf.call_args[0][0] == ["/usr/bin/keyd", "bind", "reset"]


# --- Profil ----------------------------------------------------------------


def test_profil_liest_tasten(tmp_path):
    pfad = tmp_path / "t.toml"
    pfad.write_text('[spiel]\nname = "X"\n\n[tasten]\nup = "w"\npageup = "space"\n',
                    encoding="utf-8")
    p = profil.laden(pfad)
    assert p.tasten == {"up": "w", "pageup": "space"}


def test_profil_lehnt_zahlen_ab(tmp_path):
    """Rechts muss Text stehen. ``up = 5`` ist keine Taste."""
    pfad = tmp_path / "t.toml"
    pfad.write_text('[spiel]\nname = "X"\n\n[tasten]\nup = 5\n', encoding="utf-8")
    with pytest.raises(profil.ProfilFehler):
        profil.laden(pfad)


def test_profil_ohne_tasten_hat_leere_abbildung(tmp_path):
    pfad = tmp_path / "t.toml"
    pfad.write_text('[spiel]\nname = "X"\n', encoding="utf-8")
    assert profil.laden(pfad).tasten == {}
