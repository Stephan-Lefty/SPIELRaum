"""Prüft die Auswertung der Messprotokolle.

Die Beispiele haben den Aufbau echter MangoHud-Dateien (0.8.4, nachgesehen
am 30.09.2026): zwei Kopfzeilen mit Angaben zum Rechner, dann erst die
Spaltennamen, und ``elapsed`` in Nanosekunden.
"""

import pytest

from spielraum import messen

KOPF = (
    "os,cpu,gpu,ram,kernel,driver,cpuscheduler\n"
    "Test Linux,Test-Prozessor,Test-Grafik,32800000,6.0.0-test,,powersave\n"
    "fps,frametime,cpu_load,gpu_load,elapsed\n"
)


def log_schreiben(ordner, name, werte, abstand_ms=100, cpu=20.0, kopf=KOPF):
    """Ein Protokoll erzeugen; ``werte`` sind die Bildraten der Reihe nach.

    ``cpu`` darf eine Zahl sein (gilt für alle Stichproben) oder eine Liste
    gleicher Länge wie ``werte`` -- für die Fälle, in denen die CPU-Last
    mitten im Lauf springt, weil ein Mitläufer aufhört.
    """
    zeilen = [kopf]
    for nummer, fps in enumerate(werte, start=1):
        elapsed = nummer * abstand_ms * 1_000_000  # ms -> ns
        last = cpu[nummer - 1] if isinstance(cpu, list) else cpu
        zeilen.append(f"{fps},16.0,{last},50.0,{elapsed}\n")
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
    assert k.mittel == pytest.approx(50.0)
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


def test_aussetzer_werden_auch_ohne_ladezeit_gemeldet(tmp_path):
    """Der Anzeigefehler vom 01.10.2026.

    Die Zeile mit den Aussetzern hing an der Bedingung für die Ladezeit.
    Lud ein Spiel in unter einer Sekunde – etwa weil es kurz zuvor schon
    lief und im Zwischenspeicher lag –, verschwanden die Aussetzer aus der
    Anzeige, obwohl sie gezählt waren. Ein Lauf mit 49 solchen Stichproben
    meldete nichts.
    """
    # Lädt sofort, hat aber mittendrin Hänger.
    werte = [50.0] * 200 + [0.3] * 40 + [50.0] * 200
    k = messen.auswerten(messen.lesen(log_schreiben(tmp_path, "l", werte)))
    assert k.ladezeit < 1
    assert k.aussetzer == 40
    assert "Aussetzer" in str(k)


def test_ladezeit_ohne_aussetzer_bleibt_lesbar(tmp_path):
    werte = [2.81111e-05] * 240 + [50.0] * 300
    k = messen.auswerten(messen.lesen(log_schreiben(tmp_path, "l", werte)))
    text = str(k)
    assert "Ladezeit" in text
    assert "Aussetzer" not in text
    assert ", dazu" not in text  # kein Komma ins Leere


# --- Mitläufer erkennen ----------------------------------------------------
#
# Anlass: Am 12.11.2026 nahm OBS während eines Messlaufs von Road to Vostok
# auf und kostete 17 % Bildrate. Die Messung war wertlos, aber es stand in
# der Datei -- cpu_load 68,9 % gegen 26 bis 29 % in den sauberen Läufen.
# Niemand hat hingesehen, und zwei falsche Schlüsse landeten im Repo.


def test_cpu_last_kommt_aus_dem_messfenster_nicht_aus_dem_ganzen_lauf(tmp_path):
    """Die Ladephase hat hohe CPU-Last, ganz ohne Mitläufer.

    Rechnete die CPU-Last über den ganzen Lauf, wäre jedes Spiel mit
    langer Ladezeit verdächtig.
    """
    werte = [2.81111e-05] * 240 + [50.0] * 300
    lasten = [90.0] * 240 + [20.0] * 300
    k = messen.auswerten(messen.lesen(
        log_schreiben(tmp_path, "l", werte, cpu=lasten)))
    assert k.cpu_last == pytest.approx(20.0)


def test_fehlende_cpu_spalte_ist_kein_fehler(tmp_path):
    """Ohne die Spalte gibt es keine Prüfung -- aber sehr wohl eine Messung.

    Sonst hinge die Bildrate an einer MangoHud-Einstellung, die mit ihr
    nichts zu tun hat.
    """
    ohne = ("os,cpu,gpu,ram,kernel,driver,cpuscheduler\n"
            "Test Linux,Test-Prozessor,Test-Grafik,32800000,6.0.0-test,,powersave\n"
            "fps,frametime,gpu_load,elapsed\n")
    pfad = tmp_path / "ohne.csv"
    pfad.write_text(ohne + "".join(
        f"50.0,16.0,50.0,{n * 100_000_000}\n" for n in range(1, 301)),
        encoding="utf-8")
    k = messen.auswerten(messen.lesen(pfad))
    assert k is not None
    assert k.mittel == pytest.approx(50.0)
    assert k.cpu_last == pytest.approx(0.0)
    assert "CPU-Last" not in str(k)


def test_unlesbare_cpu_zelle_verschiebt_die_zuordnung_nicht(tmp_path):
    """Eine kaputte Zelle darf die Listen nicht gegeneinander verrutschen
    lassen -- ``auswerten`` schneidet über den Index."""
    werte = [2.81111e-05] * 100 + [50.0] * 300
    zeilen = [KOPF]
    for nummer, fps in enumerate(werte, start=1):
        # Jede zehnte Zelle ist Müll, und zwar in der Ladephase wie danach.
        last = "" if nummer % 10 == 0 else (90.0 if nummer <= 100 else 20.0)
        zeilen.append(f"{fps},16.0,{last},50.0,{nummer * 100_000_000}\n")
    pfad = tmp_path / "kaputt.csv"
    pfad.write_text("".join(zeilen), encoding="utf-8")

    m = messen.lesen(pfad)
    assert len(m.cpu_last) == len(m.bilder)  # Gleichlauf gewahrt
    k = messen.auswerten(m)
    assert k.cpu_last == pytest.approx(20.0)  # nicht 90, nichts dazwischen


def test_mitlaeufer_wird_beim_vergleich_gemeldet(tmp_path):
    """Der Fall vom 12.11.2026, in Zahlen nachgebaut."""
    sauber = messen.auswerten(messen.lesen(
        log_schreiben(tmp_path, "sauber", [50.0] * 6000, cpu=28.6)))
    mit_obs = messen.auswerten(messen.lesen(
        log_schreiben(tmp_path, "obs", [41.0] * 6000, cpu=68.9)))

    warnung = messen.mitlaeufer_verdacht(sauber, mit_obs)
    assert warnung is not None
    assert "40 Prozentpunkte" in warnung
    assert "zweiten" in warnung  # der mit der höheren Last

    zeilen = "\n".join(messen.vergleichen(sauber, mit_obs))
    assert "CPU-Last" in zeilen
    assert "+40.3 Punkte" in zeilen
    assert "Bildschirmaufnahme" in zeilen


def test_die_drei_sauberen_laeufe_loesen_keine_warnung_aus(tmp_path):
    """Zwischen 25,7 und 28,6 Prozent liegt keine Aussage.

    Die echten Werte vom 05., 09. und 10.11.2026. Wäre die Schwelle so
    knapp, dass diese drei sich gegenseitig verdächtigen, wäre sie
    unbrauchbar.
    """
    kennzahlen = [
        messen.auswerten(messen.lesen(
            log_schreiben(tmp_path, f"l{i}", [50.0] * 6000, cpu=last)))
        for i, last in enumerate((26.1, 25.7, 28.6))
    ]
    for a in kennzahlen:
        for b in kennzahlen:
            assert messen.mitlaeufer_verdacht(a, b) is None


def test_ohne_cpu_last_keine_warnung(tmp_path):
    """Nicht mitgeschrieben heißt nicht verdächtig."""
    mit = messen.auswerten(messen.lesen(
        log_schreiben(tmp_path, "mit", [50.0] * 6000, cpu=70.0)))
    ohne = messen.Kennzahlen(mittel=50.0, tief_1=50.0, tief_01=50.0,
                             stichproben=6000, dauer=600.0, verworfen=0)
    assert messen.mitlaeufer_verdacht(mit, ohne) is None
    assert messen.mitlaeufer_verdacht(ohne, mit) is None


def test_zu_kurze_laeufe_loesen_keine_warnung_aus(tmp_path):
    """Der Fehler vom 12.11.2026, gefunden beim Nachsehen in der Oberfläche.

    Die Warnung stützte sich auf einen Lauf von 13 Sekunden und meldete
    42 Prozentpunkte, wo in den brauchbaren Läufen 32 lagen -- also genau
    der Fehler, den sie verhindern soll: eine Zahl aus zu wenig Material.
    """
    # 130 Stichproben à 100 ms = 13 Sekunden, wie der echte Lauf.
    kurz = messen.auswerten(messen.lesen(
        log_schreiben(tmp_path, "kurz", [57.9] * 130, cpu=16.9)))
    assert kurz is not None, "der Lauf soll auswertbar bleiben"
    assert kurz.cpu_last == pytest.approx(16.9), \
        "die CPU-Last wird trotzdem ausgewiesen"

    lang = messen.auswerten(messen.lesen(
        log_schreiben(tmp_path, "lang", [46.9] * 6000, cpu=59.1)))
    assert messen.mitlaeufer_verdacht(kurz, lang) is None
    assert messen.mitlaeufer_verdacht(lang, kurz) is None

    # Zwei lange Läufe mit demselben Abstand sagen sehr wohl etwas.
    auch_lang = messen.auswerten(messen.lesen(
        log_schreiben(tmp_path, "auchlang", [48.4] * 6000, cpu=26.7)))
    assert messen.mitlaeufer_verdacht(auch_lang, lang) is not None
