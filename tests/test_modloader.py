"""Prüft das Aktuellhalten des Mod Loaders.

**Hier geht nichts ins Netz.** Jeder Abruf wird ersetzt; ein Test, der eine
Veröffentlichung auf GitHub braucht, ist am Tag nach der nächsten
Veröffentlichung rot und sagt nichts über den Code aus.

Der wichtigste Test ist ``test_falsche_fassung_wird_nicht_eingebaut``: Was
aus dem Netz kommt, landet in einem Spielordner. Wenn dabei etwas anderes
ankommt als bestellt, darf es dort nicht hin.
"""

from pathlib import Path
from unittest import mock

import pytest

from spielraum import modloader, umgebung

QUELLE = modloader.QUELLEN["vostok"]


def loader_text(fassung: str, fuellung: int = modloader.MINDESTGROESSE) -> str:
    """Eine glaubwürdige modloader.gd – groß genug, mit Fassungszeile."""
    kopf = f'const MODLOADER_VERSION := "{fassung}"\n'
    return kopf + "# Füllung\n" * (fuellung // 11)


@pytest.fixture
def ordner(tmp_path, monkeypatch):
    """Zwischenlager und Spielordner in den Testordner umlenken."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "daten"))
    umgebung.ermitteln.cache_clear()
    spiel = tmp_path / "spiel"
    spiel.mkdir()
    sicherungen = tmp_path / "sicherungen"
    return spiel, sicherungen


# --- Fassungen vergleichen -------------------------------------------------


def test_fassung_wird_aus_der_datei_gelesen(ordner):
    spiel, _ = ordner
    ziel = spiel / "modloader.gd"
    ziel.write_text(loader_text("3.2.1"), encoding="utf-8")
    assert modloader.installierte_fassung(QUELLE, ziel) == "3.2.1"


def test_fehlende_datei_ist_kein_absturz(ordner):
    spiel, _ = ordner
    assert modloader.installierte_fassung(QUELLE, spiel / "gibtsnicht.gd") is None


def test_vergleich_rechnet_nach_zahlen_nicht_nach_text():
    """»3.10.0« ist neuer als »3.9.0«, obwohl »1« vor »9« kommt.

    Der Fall, an dem ein Textvergleich scheitert – und er kommt bei jedem
    Projekt irgendwann.
    """
    assert modloader.vergleichen("3.10.0", "3.9.0") > 0
    assert modloader.vergleichen("3.9.0", "3.10.0") < 0


def test_vergleich_ignoriert_das_v():
    """GitHub markiert »v3.4.2«, in der Datei steht »3.4.2«."""
    assert modloader.vergleichen("v3.4.2", "3.4.2") == 0


def test_vergleich_erkennt_den_echten_rueckstand():
    """Der Anlass vom 04.11.2026: 3.2.1 installiert, 3.4.2 veröffentlicht."""
    assert modloader.vergleichen("3.4.2", "3.2.1") > 0


def test_unterschiedlich_viele_stellen():
    assert modloader.vergleichen("3.4", "3.4.0") == 0
    assert modloader.vergleichen("3.4.1", "3.4") > 0


# --- Herunterladen ---------------------------------------------------------


def test_falsche_fassung_wird_nicht_eingebaut(ordner):
    """Bestellt ist 3.4.2, geliefert wird 3.3.0 – dann nichts.

    Die Datei landet in einem Spielordner. Dass *etwas* ankam, genügt nicht;
    es muss das sein, was GitHub als Veröffentlichung nennt. Das fängt eine
    Veröffentlichung ab, deren Anhang nicht zu ihrer Marke passt.
    """
    with mock.patch.object(modloader, "_holen",
                           return_value=loader_text("3.3.0").encode()):
        with pytest.raises(modloader.ModLoaderFehler) as fehler:
            modloader.herunterladen(QUELLE, "3.4.2")
    assert "3.4.2" in str(fehler.value) and "3.3.0" in str(fehler.value)


def test_fehlerseite_wird_nicht_eingebaut(ordner):
    """Eine HTML-Fehlerseite ist klein – daran erkennt man sie."""
    with mock.patch.object(modloader, "_holen", return_value=b"<html>404</html>"):
        with pytest.raises(modloader.ModLoaderFehler) as fehler:
            modloader.herunterladen(QUELLE, "3.4.2")
    assert "Bytes" in str(fehler.value)


def test_datei_ohne_fassungszeile_wird_abgelehnt(ordner):
    with mock.patch.object(modloader, "_holen",
                           return_value=b"# nur Text\n" * 9000):
        with pytest.raises(modloader.ModLoaderFehler) as fehler:
            modloader.herunterladen(QUELLE, "3.4.2")
    assert "keine" in str(fehler.value)


def test_heruntergeladenes_landet_im_zwischenlager_nicht_im_spiel(ordner):
    """Herunterladen darf am Spiel nichts ändern.

    Solange nichts bestätigt ist, hat die neue Fassung im Spielordner nichts
    zu suchen – sonst wäre »geholt« schon »eingebaut«.
    """
    spiel, _ = ordner
    ziel = spiel / "modloader.gd"
    ziel.write_text(loader_text("3.2.1"), encoding="utf-8")

    with mock.patch.object(modloader, "_holen",
                           return_value=loader_text("3.4.2").encode()):
        lager = modloader.herunterladen(QUELLE, "3.4.2")

    assert lager.is_file()
    assert modloader.zwischenlager() in lager.parents
    assert modloader.installierte_fassung(QUELLE, ziel) == "3.2.1"


# --- Prüfen ----------------------------------------------------------------


def test_pruefen_verschluckt_netzfehler(ordner):
    """Ohne Netz keine Ausnahme, sondern eine Auskunft.

    Diese Funktion läuft im Hintergrund eines Spielstarts. Ein
    Ausnahmefehler dort hätte mit dem Spiel nichts zu tun und würde es
    trotzdem treffen.
    """
    spiel, _ = ordner
    ziel = spiel / "modloader.gd"
    ziel.write_text(loader_text("3.2.1"), encoding="utf-8")

    with mock.patch.object(modloader, "_holen",
                           side_effect=modloader.ModLoaderFehler("kein Netz")):
        stand = modloader.pruefen(QUELLE, ziel)

    assert stand.installiert == "3.2.1"
    assert stand.grund == "kein Netz"
    assert stand.veraltet is False


def test_aktuelle_fassung_gilt_nicht_als_veraltet(ordner):
    spiel, _ = ordner
    ziel = spiel / "modloader.gd"
    ziel.write_text(loader_text("3.4.2"), encoding="utf-8")

    with mock.patch.object(modloader, "neueste_fassung", return_value="3.4.2"):
        stand = modloader.pruefen(QUELLE, ziel)
    assert stand.veraltet is False
    assert stand.bereit is None


def test_stand_lokal_fragt_nicht_nach(ordner):
    """Die Oberfläche soll etwas zeigen können, ohne auf das Netz zu warten."""
    spiel, _ = ordner
    ziel = spiel / "modloader.gd"
    ziel.write_text(loader_text("3.2.1"), encoding="utf-8")

    with mock.patch.object(modloader, "_holen",
                           side_effect=AssertionError("hat doch gefragt")):
        stand = modloader.stand_lokal(QUELLE, ziel)
    assert stand.installiert == "3.2.1"


# --- Einbauen und zurücknehmen ---------------------------------------------


def test_einbauen_sichert_die_alte_fassung(ordner):
    spiel, sicherungen = ordner
    ziel = spiel / "modloader.gd"
    ziel.write_text(loader_text("3.2.1"), encoding="utf-8")

    with mock.patch.object(modloader, "_holen",
                           return_value=loader_text("3.4.2").encode()):
        modloader.herunterladen(QUELLE, "3.4.2")
    modloader.einbauen(QUELLE, ziel, "3.4.2", sicherungen)

    assert modloader.installierte_fassung(QUELLE, ziel) == "3.4.2"
    gesichert = modloader.sicherungen(QUELLE, sicherungen)
    assert len(gesichert) == 1
    assert "3.2.1" in gesichert[0].name


def test_zuruecknehmen_holt_die_alte_fassung_zurueck(ordner):
    """Der Weg zurück muss stehen, bevor man das Update wagt."""
    spiel, sicherungen = ordner
    ziel = spiel / "modloader.gd"
    ziel.write_text(loader_text("3.2.1"), encoding="utf-8")

    with mock.patch.object(modloader, "_holen",
                           return_value=loader_text("3.4.2").encode()):
        modloader.herunterladen(QUELLE, "3.4.2")
    modloader.einbauen(QUELLE, ziel, "3.4.2", sicherungen)
    modloader.zuruecknehmen(QUELLE, ziel, sicherungen)

    assert modloader.installierte_fassung(QUELLE, ziel) == "3.2.1"


def test_zuruecknehmen_ohne_sicherung_erklaert_sich(ordner):
    spiel, sicherungen = ordner
    ziel = spiel / "modloader.gd"
    ziel.write_text(loader_text("3.2.1"), encoding="utf-8")
    with pytest.raises(modloader.ModLoaderFehler) as fehler:
        modloader.zuruecknehmen(QUELLE, ziel, sicherungen)
    assert "keine gesicherte Fassung" in str(fehler.value)


def test_einbauen_ohne_zwischenlager_bricht_ab(ordner):
    """Eingebaut wird nur, was geprüft dalag."""
    spiel, sicherungen = ordner
    ziel = spiel / "modloader.gd"
    ziel.write_text(loader_text("3.2.1"), encoding="utf-8")
    with pytest.raises(modloader.ModLoaderFehler) as fehler:
        modloader.einbauen(QUELLE, ziel, "3.4.2", sicherungen)
    assert "Zwischenlager" in str(fehler.value)


# --- Profil ----------------------------------------------------------------


def test_profil_nimmt_nur_bekannte_quellen(tmp_path):
    """Im Profil steht eine Kennung, keine Adresse.

    Eine Profildatei kann jeder bearbeiten. Stünde dort eine URL, aus der
    SPIELRaum etwas ins Spielverzeichnis lädt, wäre das ein Weg hinein –
    dieselbe Überlegung wie bei [tasten].
    """
    from spielraum import profil

    pfad = tmp_path / "t.toml"
    pfad.write_text('[spiel]\nname = "X"\n\n[modloader]\nquelle = "vostok"\n',
                    encoding="utf-8")
    assert profil.laden(pfad).modloader == "vostok"

    pfad.write_text(
        '[spiel]\nname = "X"\n\n[modloader]\n'
        'quelle = "https://beliebig.example/boese.gd"\n', encoding="utf-8")
    with pytest.raises(profil.ProfilFehler) as fehler:
        profil.laden(pfad)
    assert "kennt SPIELRaum nicht" in str(fehler.value)


def test_profil_ohne_abschnitt_ist_aus(tmp_path):
    from spielraum import profil

    pfad = tmp_path / "t.toml"
    pfad.write_text('[spiel]\nname = "X"\n', encoding="utf-8")
    assert profil.laden(pfad).modloader == ""
