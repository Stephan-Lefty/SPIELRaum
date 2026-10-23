"""Das Spiel starten, begleiten und hinterher aufräumen.

Der Ablauf ist kurz. Interessant ist nicht, was im Normalfall passiert,
sondern was passiert, wenn etwas schiefgeht – und davon gibt es hier mehr
Fälle als üblich, weil zwischen Start und Ende ein fremdes Programm liegt,
das abstürzen, hängen oder abgeschossen werden kann.

Die Fälle und was jeweils greift:

==============================  =========================================
Das Spiel endet normal          ``finally`` setzt zurück
Das Spiel stürzt ab             dasselbe – ein Absturz ist ein Ende
SPIELRaum bekommt SIGTERM       Signalbehandlung reicht weiter, dann
                                ``finally``
SPIELRaum bekommt SIGKILL       nichts greift – dafür liegt das Journal
                                auf der Platte, der nächste Start räumt auf
Der Rechner geht hart aus       dasselbe
==============================  =========================================

Nur der letzte Fall braucht das Journal wirklich. Genau deshalb gibt es
sowohl das ``finally`` als auch das Journal: Das eine ist der schnelle Weg,
das andere das Netz darunter.

**Als Steam-Wrapper.** In den Startoptionen eines Spiels::

    spielraum starten %command%

Steam ersetzt ``%command%`` durch den ganzen Startbefehl samt Proton. Alles
nach ``starten`` ist deshalb der zu startende Befehl und wird unverändert
durchgereicht – SPIELRaum legt nur etwas davor und setzt die Umgebung.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from . import fahrt, stellschrauben, steam, tasten, umgebung, zustand
from .profil import Profil


def spiel_ermitteln(profil: Profil) -> steam.Spiel | None:
    """Wo liegt das Spiel zu diesem Profil gerade?

    »Gerade« ist das Entscheidende: Es wird bei jedem Start neu gesucht, nie
    aus dem Profil gelesen. Ein Spiel, das deinstalliert und neu geladen
    wurde, liegt womöglich in einer anderen Bibliothek.
    """
    if profil.steam_app_id is None:
        return None
    for spiel in steam.spiele_finden():
        if spiel.app_id == profil.steam_app_id:
            return spiel
    return None


def messmarke(profil: Profil) -> Path:
    """Die Datei, die sagt: Der nächste Start ist ein Messlauf.

    Sie gibt es, weil in den Steam-Startoptionen ``spielraum starten
    %command%`` steht - ohne Angabe einer Dauer. Wer für einen Messlauf die
    Startoptionen ändern müsste, vergisst es hinterher zurückzustellen.

    Die Marke gilt für **einen** Start und wird dabei verbraucht. Das ist
    Absicht: Eine vergessene Marke blendete sonst bei jedem Spielen eine
    sinnlose Uhr ein.
    """
    return umgebung.daten_verzeichnis() / f"messlauf-{profil.steam_app_id or profil.name}.json"


def marke_setzen(profil: Profil, minuten: float) -> Path:
    import json

    pfad = messmarke(profil)
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_text(json.dumps({"minuten": minuten}), encoding="utf-8")
    return pfad


def marke_lesen(profil: Profil) -> float | None:
    """Die Marke lesen und verbrauchen."""
    import json

    pfad = messmarke(profil)
    try:
        minuten = float(json.loads(pfad.read_text(encoding="utf-8"))["minuten"])
    except (OSError, ValueError, KeyError, TypeError):
        return None
    pfad.unlink(missing_ok=True)
    return minuten


def starten(profil: Profil, befehl: list[str], trocken: bool = False,
            minuten: float | None = None) -> int:
    """Anwenden, starten, warten, zurücksetzen.

    ``trocken`` zeigt nur, was geschähe. Das ist kein Beiwerk: Wer einem
    Programm erlaubt, in die Dateien seiner Spiele zu schreiben, soll vorher
    nachsehen dürfen.
    """
    if not befehl:
        print("Kein Startbefehl übergeben.", file=sys.stderr)
        return 2

    spiel = spiel_ermitteln(profil)
    spielordner = spiel.ordner if spiel else None
    praefix = spiel.proton_praefix if spiel else None

    journal = zustand.Journal(spiel=profil.name, pid=os.getpid())
    messen_in = stellschrauben.messordner() / f"{profil.steam_app_id or profil.name}"

    voller_befehl = stellschrauben.befehl_umhuellen(profil, befehl)

    # Läuft eine Messfahrt? Dann setzt dieser Start die nächste Variante.
    # Geführt wird die Fahrt in der Oberfläche; hier wird nur ausgeführt,
    # was in der Akte steht – und hinterher das Ergebnis zurückgeschrieben.
    laufende_fahrt = None
    fahrt_variante = None
    if profil.steam_app_id and not trocken:
        laufende_fahrt = fahrt.lesen(profil.steam_app_id)

        # Automatik: Steht »fahrt = true« im Profil und gibt es noch keine
        # Akte, beginnt hier eine. Danach nie wieder von selbst -- die
        # abgeschlossene Akte bleibt als Merker liegen. Ohne den begänne
        # nach jedem Verwerfen sofort die nächste Fahrt.
        auswahl = [n for n in profil.fahrt_varianten if n in profil.varianten] \
            or list(profil.varianten)
        if (laufende_fahrt is None and profil.fahrt_automatisch
                and len(auswahl) >= 2):
            laufende_fahrt = fahrt.Fahrt(
                spiel=profil.name, steam_app_id=profil.steam_app_id,
                varianten=auswahl, angelegt=time.time())
            fahrt.schreiben(laufende_fahrt)
            print(f"Messfahrt begonnen: {len(auswahl)} Läufe zu je "
                  f"{fahrt.MINDESTDAUER / 60:.0f} Minuten. Abbrechen mit: "
                  f"spielraum messfahrt {profil.steam_app_id} --abbrechen")

        if laufende_fahrt is not None:
            if laufende_fahrt.abgeschlossen:
                # Durch und entschieden. Nicht anfassen.
                laufende_fahrt = None
            else:
                fahrt_variante = laufende_fahrt.naechste
                if fahrt_variante is None:
                    # Alle Läufe erledigt, aber noch nichts entschieden. Die
                    # Akte bleibt liegen, bis jemand übernimmt oder verwirft –
                    # sonst wäre das Ergebnis nach dem letzten Lauf weg.
                    laufende_fahrt = None

    # Läuft eine Messung über eine feste Dauer, blendet MangoHud die
    # Restzeit ein. Die Variante steht mit im Bild - sonst weiß man nach
    # dem dritten Lauf nicht mehr, welcher gerade dran ist.
    if minuten is None and not trocken:
        minuten = marke_lesen(profil)
    # Während einer Messfahrt ist die Mindestdauer vorgegeben. Ohne
    # Restzeit im Bild müsste man im Vollbild raten, wann zehn Minuten um
    # sind – und Alt-Tab zum Nachsehen verfälscht die Messung.
    if laufende_fahrt is not None and not minuten:
        minuten = fahrt.MINDESTDAUER / 60

    laeuft_bis = None
    ueberschrift = ""
    if minuten:
        from . import varianten as varianten_modul

        laeuft_bis = time.time() + minuten * 60
        if laufende_fahrt is not None:
            nummer = sum(1 for l in laufende_fahrt.laeufe if l.zaehlt) + 1
            ueberschrift = (f"SPIELRaum: Messfahrt {nummer}/"
                            f"{len(laufende_fahrt.varianten)} – {fahrt_variante}")
        else:
            jetzt = varianten_modul.aktuelle(profil, spielordner, praefix)
            ueberschrift = f"SPIELRaum: {jetzt or 'eigene Einstellung'}"

    laufumgebung = stellschrauben.umgebung_bauen(
        profil, messen_in if profil.mangohud else None,
        laeuft_bis=laeuft_bis, ueberschrift=ueberschrift,
    )

    if trocken:
        print(f"Profil:  {profil.name}")
        print(f"Spiel:   {spielordner or 'nicht gefunden'}")
        print(f"Befehl:  {' '.join(voller_befehl)}")
        geaendert = {k: v for k, v in profil.variablen.items()}
        if profil.mangohud and "MANGOHUD" in laufumgebung:
            geaendert["MANGOHUD"] = laufumgebung["MANGOHUD"]
            geaendert["MANGOHUD_CONFIG"] = laufumgebung.get("MANGOHUD_CONFIG", "")
        for name, wert in geaendert.items():
            print(f"  {name}={wert}")
        for kennung, aenderung in profil.dateien.items():
            print(f"  Datei {kennung}: {aenderung.pfad}")
        for taste, ziel in profil.tasten.items():
            print(f"  Taste {taste} → {ziel}")
        print("\nProbelauf – es wurde nichts geändert und nichts gestartet.")
        return 0

    for warnung in profil.warnungen():
        print(f"Hinweis: {warnung}", file=sys.stderr)

    rueckgabe = 1
    vorher_bekannt = sorted(messen_in.glob("*.csv")) if messen_in.is_dir() else []
    try:
        getan = stellschrauben.dateien_anwenden(
            profil, journal, spielordner, praefix, variante=fahrt_variante)
        if fahrt_variante:
            print(f"Messfahrt: Lauf mit Variante »{fahrt_variante}«")

        # Tastenbelegung. Scheitert sie, startet das Spiel trotzdem: Eine
        # fehlende Gruppenmitgliedschaft ist ärgerlich, aber kein Grund,
        # jemanden vom Spielen abzuhalten. Er soll nur wissen, warum die
        # Tasten anders liegen als erwartet.
        if profil.tasten:
            try:
                getan += [f"Taste {z}" for z in tasten.setzen(profil.tasten, journal)]
            except tasten.TastenFehler as fehler:
                print(f"Tastenbelegung ausgefallen: {fehler}", file=sys.stderr)

        # Das Journal muss liegen, bevor der erste Prozess startet. Fällt der
        # Strom danach aus, ist es die einzige Spur dessen, was verstellt war.
        zustand.schreiben(journal)
        for zeile in getan:
            print(f"Angepasst: {zeile}")

        rueckgabe = _laufen_lassen(voller_befehl, laufumgebung, profil)
    except Exception as fehler:  # noqa: BLE001 – hier ist Weitermachen falsch
        print(f"Abbruch: {fehler}", file=sys.stderr)
    finally:
        # Erst den Lauf bewerten, dann zurücksetzen. Andersherum stünde in
        # der Einstellungsdatei schon wieder der alte Wert, und die Prüfung
        # »waren die Einstellungen während des Laufs unverändert?« ginge ins
        # Leere.
        if laufende_fahrt is not None:
            _fahrt_auswerten(laufende_fahrt, fahrt_variante, messen_in, vorher_bekannt)

        bericht = stellschrauben.zuruecksetzen(journal)
        for zeile in bericht:
            print(f"Zurückgesetzt: {zeile}")
        zustand.entfernen(profil.name)

    return rueckgabe


def _fahrt_auswerten(laufende: "fahrt.Fahrt", variante: str, messen_in: Path,
                     vorher_bekannt: list[Path]) -> None:
    """Den eben gespielten Lauf bewerten und in die Fahrtenakte eintragen.

    Gesucht wird die Messdatei, die es vorher noch nicht gab – nicht die
    neueste. Wer zwischendurch ein anderes Spiel misst, bekäme sonst dessen
    Zahlen in seine Fahrtenakte.
    """
    from . import messen

    neu = [p for p in sorted(messen_in.glob("*.csv")) if p not in vorher_bekannt]
    eintrag = fahrt.Lauf(variante=variante)

    if not neu:
        eintrag.verworfen = ("Keine Messdatei entstanden. Läuft MangoHud, und "
                             "steht »mangohud = true« im Profil?")
    else:
        messung = messen.lesen(neu[-1])
        kennzahlen = messen.auswerten(messung)
        grund = fahrt.pruefen(kennzahlen)
        if grund:
            eintrag.verworfen = grund
            eintrag.dauer = kennzahlen.dauer if kennzahlen else 0.0
        else:
            eintrag.messdatei = neu[-1].name
            eintrag.mittel = kennzahlen.mittel
            eintrag.tief_1 = kennzahlen.tief_1
            eintrag.tief_01 = kennzahlen.tief_01
            eintrag.dauer = kennzahlen.dauer

    laufende.vermerken(eintrag)
    fahrt.schreiben(laufende)

    if eintrag.zaehlt:
        print(f"Messfahrt: »{variante}« gezählt – {eintrag.mittel:.1f} Bilder/s, "
              f"1-%-Tief {eintrag.tief_1:.1f}")
        rest = laufende.naechste
        print(f"Messfahrt: {laufende.stand} Läufen erledigt"
              + (f", als Nächstes »{rest}«" if rest else " – alle fertig"))
    else:
        print(f"Messfahrt: »{variante}« zählt nicht. {eintrag.verworfen}",
              file=sys.stderr)


def _laufen_lassen(befehl: list[str], laufumgebung: dict[str, str], profil: Profil) -> int:
    """Den Prozess starten und auf ihn warten – Signale weiterreichen.

    Ohne die Signalbehandlung gäbe es einen hässlichen Fall: Beim Abmelden
    schickt systemd SIGTERM. Python bräche dann sofort ab, das Spiel liefe
    als verwaister Prozess weiter, und zurückgesetzt würde zu früh. Mit ihr
    bekommt das Spiel das Signal, SPIELRaum wartet sein Ende ab und räumt
    danach auf.
    """
    prozess = subprocess.Popen(befehl, env=laufumgebung)
    begonnen = time.monotonic()

    def weiterreichen(signalnummer, _rahmen):
        try:
            prozess.send_signal(signalnummer)
        except ProcessLookupError:
            pass

    alte = {}
    for nummer in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        try:
            alte[nummer] = signal.signal(nummer, weiterreichen)
        except (ValueError, OSError):
            pass

    try:
        rueckgabe = prozess.wait()
    finally:
        for nummer, behandlung in alte.items():
            try:
                signal.signal(nummer, behandlung)
            except (ValueError, OSError):
                pass

    dauer = time.monotonic() - begonnen
    print(f"{profil.name} beendet nach {dauer / 60:.1f} Minuten (Rückgabe {rueckgabe}).")
    return rueckgabe


def aufraeumen(nur_zeigen: bool = False) -> int:
    """Journale abarbeiten, die ein Absturz hinterlassen hat.

    Liegende Messfahrten werden dabei nur gemeldet, nicht beendet: Eine
    Fahrt ist kein Unfall, sondern Absicht, und zwischen zwei Läufen können
    Tage liegen. Gemeldet werden muss sie trotzdem -- wer nach drei Wochen
    wieder spielt, erinnert sich nicht daran und wundert sich sonst über
    fremde Grafikeinstellungen.
    """
    for offene in fahrt.alle():
        print(f"Messfahrt unterwegs: {offene.spiel} – {offene.stand} Läufen "
              f"erledigt" + (f", als Nächstes »{offene.naechste}«"
                             if offene.naechste else ", alle fertig"))
        print(f"    Ansehen oder beenden:  spielraum messfahrt "
              f"{offene.steam_app_id}")

    verwaist = zustand.verwaiste_journale()
    if not verwaist:
        print("Keine liegengebliebenen Journale.")
        return 0

    for journal in verwaist:
        print(f"Verwaistes Journal: {journal.spiel} (Prozess {journal.pid} lebt nicht mehr)")
        if nur_zeigen:
            for eintrag in journal.eintraege:
                ziel = "entfernen" if eintrag.vorher is None else f"aus {eintrag.vorher}"
                print(f"    {eintrag.ziel}: {ziel}")
            continue
        for zeile in stellschrauben.zuruecksetzen(journal):
            print(f"    {zeile}")
        zustand.entfernen(journal.spiel)

    if nur_zeigen:
        print("\nNur angezeigt. Ohne --zeigen wird zurückgesetzt.")
    return 0
