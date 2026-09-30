"""Prüft die Auswertung der Messprotokolle.

Die Beispiele haben den Aufbau echter MangoHud-Dateien (0.8.4, nachgesehen
am 30.09.2026): zwei Kopfzeilen mit Angaben zum Rechner, dann erst die
Spaltennamen, und ``elapsed`` in Nanosekunden.
"""

from spielraum import messen

KOPF = (
    "os,cpu,gpu,ram,kernel,driver,cpuscheduler\n"
    "Test Linux,Test-Prozessor,Test-Grafik,32800000,6.0.0-test,,powersave\n"
    "fps,frametime,cpu_load,gpu_load,elapsed\n"
)


def log_schreiben(ordner, name, werte, abstand_ms=100):
    """Ein Protokoll erzeugen; ``werte`` sind die Bildraten der Reihe nach."""
    zeilen = [KOPF]
    for nummer, fps in enumerate(werte, start=1):
        elapsed = nummer * abstand_ms * 1_000_000  # ms -> ns
        zeilen.append(f"{fps},16.0,20.0,50.0,{elapsed}\n")
    pfad = ordner / f"{name}.csv"
    pfad.write_text("".join(zeilen), encoding="utf-8")
    return pfad


def test_metadaten_werden_gelesen(tmp_path):
    """Der Taktregler steht im Protokoll – damit lässt sich nachprüfen,
    ob GameMode gegriffen hat, statt es zu glauben."""
    m = messen.lesen(log_schreiben(tmp_path, "lauf", [60.0] * 10))
    assert m.taktregler == "powersave"
    assert m.metadaten["gpu"] == "Test-Grafik"


def test_nanosekunden_werden_zu_sekunden(tmp_path):
    m = messen.lesen(log_schreiben(tmp_path, "lauf", [60.0] * 10))
    assert m.dauer == 1.0  # 10 Stichproben à 100 ms


def test_aufwaermzeit_wird_abgeschnitten(tmp_path):
    """Der Kern der Sache.

    Die ersten hundert Stichproben (zehn Sekunden) stehen auf 10 Bildern –
    so sieht ein Spiel aus, das noch Shader übersetzt. Danach 100. Wer die
    Aufwärmphase mitrechnet, kommt auf gut 70 und misst die Ladezeit.
    """
    pfad = log_schreiben(tmp_path, "lauf", [10.0] * 100 + [100.0] * 200)
    k = messen.auswerten(messen.lesen(pfad), aufwaermen=10.0)
    assert k is not None
    assert k.mittel == 100.0
    assert k.verworfen == 100

    ohne = messen.auswerten(messen.lesen(pfad), aufwaermen=0.0)
    assert 65 < ohne.mittel < 75  # das verfälschte Ergebnis


def test_zu_wenig_stichproben_gibt_keine_zahl(tmp_path):
    """Lieber keine Zahl als eine, die auf zwanzig Stichproben beruht."""
    pfad = log_schreiben(tmp_path, "kurz", [60.0] * 30)
    assert messen.auswerten(messen.lesen(pfad), aufwaermen=0.0) is None


def test_tiefstwerte(tmp_path):
    """Ein Prozent der Stichproben liegt bei 10 – das muss sich zeigen."""
    werte = [60.0] * 198 + [10.0] * 2
    k = messen.auswerten(messen.lesen(log_schreiben(tmp_path, "l", werte)), aufwaermen=0.0)
    assert k.mittel > 55
    assert k.tief_1 == 10.0  # der Ruckler, den man spürt


def test_abgeschnittene_zeile_wird_uebersprungen(tmp_path):
    """Ein hart beendetes Spiel hinterlässt eine halbe letzte Zeile – und
    genau dann will man die Messung haben."""
    pfad = log_schreiben(tmp_path, "abbruch", [60.0] * 60)
    with pfad.open("a", encoding="utf-8") as datei:
        datei.write("59.8,16.7,kaputt")
    m = messen.lesen(pfad)
    assert len(m.bilder) == 60


def test_zusammenfassungen_werden_uebergangen(tmp_path):
    log_schreiben(tmp_path, "lauf_2026-09-30", [60.0] * 60)
    (tmp_path / "lauf_2026-09-30_summary.csv").write_text(
        "Average FPS\n60.0\n", encoding="utf-8"
    )
    gefunden = messen.laeufe(tmp_path)
    assert len(gefunden) == 1
    assert not gefunden[0].name.endswith("summary")


def test_kleine_unterschiede_gelten_als_keine(tmp_path):
    """Zwei Läufe schwanken auch ohne Zutun. Ein Programm, das jede
    Schwankung als Erfolg verkauft, ist ein schlechter Ratgeber."""
    a = messen.Kennzahlen(60.0, 40.0, 30.0, 200, 30.0, 0)
    b = messen.Kennzahlen(61.0, 40.5, 30.2, 200, 30.0, 0)
    zeilen = messen.vergleichen(a, b)
    assert all("kein nennenswerter Unterschied" in z for z in zeilen)


def test_echter_gewinn_wird_benannt(tmp_path):
    a = messen.Kennzahlen(60.0, 40.0, 30.0, 200, 30.0, 0)
    b = messen.Kennzahlen(78.0, 52.0, 39.0, 200, 30.0, 0)
    zeilen = messen.vergleichen(a, b)
    assert any("+30.0 %" in z for z in zeilen)


def test_leere_datei(tmp_path):
    pfad = tmp_path / "leer.csv"
    pfad.write_text("", encoding="utf-8")
    assert messen.lesen(pfad).bilder == []
