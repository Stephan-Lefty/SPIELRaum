"""Die Kommandozeile von SPIELRaum.

Der Befehl, um den es geht, ist ``starten``. Er gehört in die Startoptionen
eines Steam-Spiels::

    spielraum starten %command%

Die übrigen Befehle sind zum Nachsehen: was auf dem Rechner liegt
(``umgebung``, ``spiele``), was eingerichtet ist (``profile``, ``pruefen``)
und was ein Absturz hinterlassen hat (``aufraeumen``).
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

from . import __version__, profil, umgebung


def _umgebung_zeigen() -> int:
    umg = umgebung.ermitteln()
    print(f"System:  {umg.name}")
    print(f"Familie: {umg.familie}")
    print()
    print("Werkzeuge:")
    for name in sorted(umgebung.PAKETE):
        pfad = umg.pfad(name)
        if pfad:
            print(f"  [ja]    {name:18} {pfad}")
        else:
            print(f"  [fehlt] {name:18} {umg.fehlt_hinweis(name)}")
    print()
    print(f"Profile:   {profil.profil_verzeichnis()}")
    print(f"Messungen: {umgebung.daten_verzeichnis() / 'messungen'}")
    print(f"Journal:   {umgebung.laufzeit_verzeichnis()}")
    return 0


def _profile_zeigen() -> int:
    verzeichnis = profil.profil_verzeichnis()
    if not verzeichnis.is_dir():
        print(f"Noch keine Profile. Sie gehören nach {verzeichnis}.")
        return 0

    dateien = sorted(verzeichnis.glob("*.toml"))
    if not dateien:
        print(f"{verzeichnis} ist leer.")
        return 0

    for datei in dateien:
        try:
            p = profil.laden(datei)
        except profil.ProfilFehler as fehler:
            print(f"  [kaputt] {datei.name}: {fehler}")
            continue
        kennung = f"Steam {p.steam_app_id}" if p.steam_app_id else "ohne Steam-ID"
        print(f"  {p.name}  ({kennung}, {datei.name})")
        for warnung in p.warnungen():
            print(f"      Hinweis: {warnung}")
    return 0


def _spiele_zeigen(alle: bool = False) -> int:
    """Was ist auf diesem Rechner installiert?

    Die Spalte »Platte« ist der Grund, warum diese Liste mehr ist als eine
    Aufzählung: Ein Spiel auf einer drehenden Platte ruckelt beim Nachladen,
    und dagegen hilft keine Einstellung – nur ein Umzug.
    """
    from . import steam

    spiele = steam.spiele_finden(mit_werkzeugen=alle)
    if not spiele:
        print("Keine installierten Spiele gefunden.")
        print("Gesucht wurde in:")
        for pfad in steam.bibliotheken():
            print(f"  {pfad}")
        return 0

    print(f"{'Spiel':30} {'App-ID':>8} {'Größe':>9}  {'Start':7} {'Platte':8} Profil")
    print("-" * 78)
    for spiel in spiele:
        dreht = umgebung.platte_dreht(spiel.ordner)
        platte = "dreht" if dreht else ("SSD" if dreht is False else "?")
        art = "Proton" if spiel.laeuft_unter_proton else "nativ"
        hat_profil = profil.finden(steam_app_id=spiel.app_id) is not None
        print(
            f"{spiel.name[:30]:30} {spiel.app_id:>8} {spiel.groesse_lesbar:>9}  "
            f"{art:7} {platte:8} {'ja' if hat_profil else '–'}"
        )

    # Profile, deren Spiel gerade nicht installiert ist. Sie gehören in die
    # Übersicht, nicht in den Papierkorb: Wer ein Spiel deinstalliert, um
    # Platz zu schaffen, und es in drei Monaten neu lädt, will seine
    # Einstellungen wiederhaben - nicht noch einmal messen.
    installiert = {s.app_id for s in spiele}
    verwaist = [
        p for p in _alle_profile()
        if p.steam_app_id is not None and p.steam_app_id not in installiert
    ]
    for p in verwaist:
        print(
            f"{p.name[:30]:30} {p.steam_app_id:>8} {'–':>9}  "
            f"{'–':7} {'–':8} ja (nicht installiert)"
        )

    ohne = [s for s in spiele if profil.finden(steam_app_id=s.app_id) is None]
    if ohne:
        print()
        print(f"{len(ohne)} Spiel(e) ohne Profil.")
    if verwaist:
        print(f"{len(verwaist)} Profil(e) warten auf ihr Spiel.")
    return 0


def _alle_profile() -> list[profil.Profil]:
    verzeichnis = profil.profil_verzeichnis()
    if not verzeichnis.is_dir():
        return []
    gefunden = []
    for datei in sorted(verzeichnis.glob("*.toml")):
        try:
            gefunden.append(profil.laden(datei))
        except profil.ProfilFehler:
            continue
    return gefunden


def _pruefen(datei: str) -> int:
    from pathlib import Path

    pfad = Path(datei)
    if not pfad.exists():
        gefunden = profil.profil_verzeichnis() / datei
        pfad = gefunden if gefunden.exists() else pfad

    try:
        p = profil.laden(pfad)
    except profil.ProfilFehler as fehler:
        print(f"Nicht in Ordnung: {fehler}", file=sys.stderr)
        return 1

    print(f"In Ordnung: {p.name}")
    if p.steam_app_id:
        print(f"  Steam-App-ID:   {p.steam_app_id}")
    if p.engine:
        print(f"  Engine:         {p.engine}")
    print(f"  GameMode:       {'ja' if p.gamemode else 'nein'}")
    print(f"  MangoHud:       {'ja' if p.mangohud else 'nein'}")
    if p.variablen:
        print(f"  Umgebung:       {len(p.variablen)} Variable(n)")
        for name, wert in p.variablen.items():
            print(f"      {name}={wert}")
    if p.argumente:
        print(f"  Argumente:      {' '.join(p.argumente)}")
    for kennung, aenderung in p.dateien.items():
        art = "zusammenführen" if aenderung.zusammenfuehren else "ERSETZEN"
        print(f"  Datei {kennung}: {aenderung.pfad} ({art})")

    for warnung in p.warnungen():
        print(f"  Hinweis: {warnung}")
    return 0


def _messungen_zeigen(welches: str | None) -> int:
    """Die Läufe eines Spiels auflisten und die letzten beiden vergleichen."""
    from . import messen, stellschrauben

    wurzel = stellschrauben.messordner()
    if not wurzel.is_dir():
        print(f"Noch nichts gemessen. Messungen entstehen unter {wurzel},")
        print("sobald ein Spiel über »spielraum starten« läuft.")
        return 0

    ordner = sorted(p for p in wurzel.iterdir() if p.is_dir())
    if welches:
        ordner = [p for p in ordner if welches.casefold() in p.name.casefold()]
    if not ordner:
        print("Keine Messungen gefunden.")
        return 0

    for spielordner in ordner:
        laeufe = messen.laeufe(spielordner)
        if not laeufe:
            continue

        name = spielordner.name
        if name.isdigit():
            gefunden = profil.finden(steam_app_id=int(name))
            if gefunden:
                name = f"{gefunden.name} ({name})"
        print(f"\n{name}")
        print("-" * len(name))

        ausgewertet = []
        for lauf in laeufe:
            kennzahlen = messen.auswerten(lauf)
            if kennzahlen is None:
                print(f"  {lauf.name}: zu kurz für eine Aussage")
                continue
            regler = f", Taktregler {lauf.taktregler}" if lauf.taktregler else ""
            print(f"  {lauf.name}{regler}")
            print(f"      {kennzahlen}")
            ausgewertet.append((lauf, kennzahlen))

        if len(ausgewertet) >= 2:
            (alt_lauf, alt), (neu_lauf, neu) = ausgewertet[-2], ausgewertet[-1]
            print(f"\n  Vergleich {alt_lauf.name}  ->  {neu_lauf.name}")
            for zeile in messen.vergleichen(alt, neu):
                print(zeile)
            if alt_lauf.taktregler != neu_lauf.taktregler:
                print(f"  Achtung: verschiedene Taktregler "
                      f"({alt_lauf.taktregler} / {neu_lauf.taktregler})")
    return 0


def _starten(args) -> int:
    """Ein Spiel mit seinem Profil starten.

    Das Profil wird in dieser Reihenfolge gesucht: was ``--profil`` sagt,
    sonst die ``SteamAppId`` aus der Umgebung. Letzteres ist der Normalfall –
    Steam setzt sie, wenn das Spiel über die Bibliothek gestartet wird, und
    sie stimmt auch dann noch, wenn das Spiel längst auf einer anderen Platte
    liegt.
    """
    from . import starten as start_modul

    # argparse.REMAINDER reicht ein trennendes »--« mit durch. Bliebe es
    # stehen, bekäme gamemoderun es als erstes Argument und stolperte
    # darüber. Steam schickt kein »--«, von Hand tippt man es aber.
    if args.befehl and args.befehl[0] == "--":
        args.befehl = args.befehl[1:]

    gefunden = None
    if args.profil:
        from pathlib import Path

        pfad = Path(args.profil)
        if not pfad.exists():
            pfad = profil.profil_verzeichnis() / args.profil
        try:
            gefunden = profil.laden(pfad)
        except profil.ProfilFehler as fehler:
            print(f"Profil unbrauchbar: {fehler}", file=sys.stderr)
            return 1
    else:
        roh = os.environ.get("SteamAppId") or os.environ.get("SteamGameId")
        if roh and roh.isdigit():
            gefunden = profil.finden(steam_app_id=int(roh))

    if gefunden is None:
        # Kein Profil ist kein Fehler: Das Spiel soll trotzdem starten.
        # Alles andere wäre eine Falle - wer SPIELRaum in die Startoptionen
        # einträgt und später das Profil löscht, käme sonst nicht mehr ins
        # Spiel und suchte den Fehler überall, nur nicht hier.
        if not args.befehl:
            print("Weder Profil noch Startbefehl. Nichts zu tun.", file=sys.stderr)
            return 2
        print("Kein Profil für dieses Spiel – es startet unverändert.", file=sys.stderr)
        return subprocess.call(args.befehl)

    return start_modul.starten(gefunden, args.befehl, trocken=args.trocken)


def _oberflaeche() -> int:
    """Die grafische Oberflaeche starten.

    Der Import steht absichtlich hier und nicht oben: Die Kommandozeile
    muss ohne PySide6 vollstaendig funktionieren - auf einem Server, in
    der CI, in einer Textkonsole.
    """
    from . import ui

    ok, meldung = ui.verfuegbar()
    if not ok:
        print(meldung, file=sys.stderr)
        return 1
    from .ui.fenster import main as fenster_main
    return fenster_main()


def _aufraeumen(nur_zeigen: bool) -> int:
    from . import starten as start_modul

    return start_modul.aufraeumen(nur_zeigen=nur_zeigen)


def main(argv: list[str] | None = None) -> int:
    zerleger = argparse.ArgumentParser(
        prog="spielraum",
        description="Spiele starten, das System dafür herrichten, hinterher aufräumen.",
    )
    zerleger.add_argument("--version", action="version", version=f"SPIELRaum {__version__}")
    unterbefehle = zerleger.add_subparsers(dest="aktion")

    unterbefehle.add_parser("umgebung", help="Was findet SPIELRaum auf diesem Rechner vor?")
    unterbefehle.add_parser("profile", help="Welche Spielprofile sind eingerichtet?")
    spiele = unterbefehle.add_parser("spiele", help="Welche Spiele sind installiert?")
    spiele.add_argument(
        "--alle", action="store_true",
        help="auch Proton und die Steam-Laufzeiten aufführen",
    )
    pruefen = unterbefehle.add_parser("pruefen", help="Eine Profildatei auf Fehler prüfen")
    pruefen.add_argument("datei", help="Pfad oder Dateiname im Profilverzeichnis")
    unterbefehle.add_parser(
        "oberflaeche", help="Die grafische Oberflaeche starten"
    )
    messungen = unterbefehle.add_parser(
        "messungen", help="Was bisher gemessen wurde – und was es gebracht hat"
    )
    messungen.add_argument(
        "spiel", nargs="?", help="auf ein Spiel einschränken (Teil des Namens genügt)"
    )

    aufraeumen = unterbefehle.add_parser(
        "aufraeumen", help="Nach einem Absturz Liegengebliebenes zurücksetzen"
    )
    aufraeumen.add_argument(
        "--zeigen", action="store_true",
        help="nur anzeigen, was zurückgesetzt würde",
    )

    start = unterbefehle.add_parser(
        "starten",
        help="Ein Spiel mit seinem Profil starten",
        description="In den Steam-Startoptionen eines Spiels: "
                    "spielraum starten %%command%%",
    )
    start.add_argument("--profil", help="Profil erzwingen statt über die Steam-App-ID")
    start.add_argument(
        "--trocken", action="store_true",
        help="nur zeigen, was geschähe – nichts ändern, nichts starten",
    )
    start.add_argument(
        "befehl", nargs=argparse.REMAINDER,
        help="der Startbefehl des Spiels (bei Steam: %%command%%)",
    )

    args = zerleger.parse_args(argv)

    if args.aktion == "umgebung":
        return _umgebung_zeigen()
    if args.aktion == "profile":
        return _profile_zeigen()
    if args.aktion == "spiele":
        return _spiele_zeigen(alle=args.alle)
    if args.aktion == "pruefen":
        return _pruefen(args.datei)
    if args.aktion == "oberflaeche":
        return _oberflaeche()
    if args.aktion == "messungen":
        return _messungen_zeigen(args.spiel)
    if args.aktion == "aufraeumen":
        return _aufraeumen(nur_zeigen=args.zeigen)
    if args.aktion == "starten":
        return _starten(args)

    zerleger.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
