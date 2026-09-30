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

from . import stellschrauben, steam, umgebung, zustand
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


def starten(profil: Profil, befehl: list[str], trocken: bool = False) -> int:
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
    laufumgebung = stellschrauben.umgebung_bauen(
        profil, messen_in if profil.mangohud else None
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
        print("\nProbelauf – es wurde nichts geändert und nichts gestartet.")
        return 0

    for warnung in profil.warnungen():
        print(f"Hinweis: {warnung}", file=sys.stderr)

    rueckgabe = 1
    try:
        getan = stellschrauben.dateien_anwenden(profil, journal, spielordner, praefix)
        # Das Journal muss liegen, bevor der erste Prozess startet. Fällt der
        # Strom danach aus, ist es die einzige Spur dessen, was verstellt war.
        zustand.schreiben(journal)
        for zeile in getan:
            print(f"Angepasst: {zeile}")

        rueckgabe = _laufen_lassen(voller_befehl, laufumgebung, profil)
    except Exception as fehler:  # noqa: BLE001 – hier ist Weitermachen falsch
        print(f"Abbruch: {fehler}", file=sys.stderr)
    finally:
        bericht = stellschrauben.zuruecksetzen(journal)
        for zeile in bericht:
            print(f"Zurückgesetzt: {zeile}")
        zustand.entfernen(profil.name)

    return rueckgabe


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
    """Journale abarbeiten, die ein Absturz hinterlassen hat."""
    verwaist = zustand.verwaiste_journale()
    if not verwaist:
        print("Nichts aufzuräumen.")
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
