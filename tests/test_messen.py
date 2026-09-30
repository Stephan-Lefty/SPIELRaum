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


def test_ladephase_wird_abgeschnitten(tmp_path):
    """Der Kern der Sache – und der Fehler aus 0.3.0.

    Die Werte in der Ladephase sind keine kleinen Bildraten, sondern
    2,8e-05 – so schreibt MangoHud es wirklich, nachgesehen an Road to
    Vostok am 30.09.2026. Bei diesem Spiel dauerte das **23,8 Sekunden**,
    weil es auf einer drehenden Platte liegt.

    Die feste Aufwärmzeit von zehn Sekunden ab Programmstart ließ die halbe
    Ladephase im Messfenster. Ergebnis: ein 1-%-Tiefstwert von 0,0 für ein
    Spiel, das durchgehend um die fünfzig Bilder lieferte.
    """
    # 240 Stichproben à 100 ms = 24 Sekunden Ladezeit, dann 300 mit 50 fps.
    pfad = log_schreiben(tmp_path, "lauf", [2.81111e-05] * 240 + [50.0] * 300)
    m = messen.lesen(pfad)

    assert 23 < messen.ladezeit(m) < 25

    k = messen.auswerten(m, aufwaermen=5.0)
    assert k is not None
    assert k.mittel == 50.0
    assert k.tief_1 == 50.0  # kein einziger Ladewert mehr drin
    assert 23 < k.ladezeit < 25


def test_feste_aufwaermzeit_haette_nicht_gereicht(tmp_path):
    """Gegenprobe zum Fehler: Von Sekunde zehn an gerechnet, liegen noch
    vierzehn Sekunden Ladephase im Fenster – und der Tiefstwert kippt."""
    werte = [2.81111e-05] * 240 + [50.0] * 300
    bilder = [f for f, s in zip(werte, (i / 10 for i in range(1, len(werte) + 1)))
              if s > 10.0]
    sortiert = sorted(bilder)
    assert sortiert[int(len(sortiert) * 0.01) - 1] < 1  # so kam die 0,0 zustande


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


def test_aussetzer_im_spiel_bleiben_drin(tmp_path):
    """Hänger *nach* dem Laden sind kein Messfehler, sondern der Befund.

    Bei Road to Vostok stand das Bild zwischen Sekunde 122 und 126 stille.
    Wer solche Werte herausrechnet, macht die Zahlen schöner und die
    Aussage wertlos.
    """
    werte = [2.81111e-05] * 100 + [50.0] * 200 + [0.034] * 40 + [50.0] * 200
    k = messen.auswerten(messen.lesen(log_schreiben(tmp_path, "l", werte)))
    assert k.aussetzer == 40
    assert k.tief_1 < 1  # der Hänger zeigt sich im Tiefstwert


def test_ladezeit_ohne_ladephase(tmp_path):
    """Ein Spiel, das sofort läuft, hat Ladezeit ~0."""
    k = messen.auswerten(messen.lesen(log_schreiben(tmp_path, "l", [60.0] * 300)))
    assert k.ladezeit < 0.2
    assert k.aussetzer == 0
