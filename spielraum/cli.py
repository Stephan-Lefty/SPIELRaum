"""Die Kommandozeile von SPIELRaum.

Hier stehen die Befehle, die bereits etwas Echtes tun. ``starten`` fehlt noch
und wird bewusst nicht als Platzhalter angeboten: Ein Befehl, der so aussieht,
als würde er das System herrichten, es aber nicht tut, ist schlimmer als gar
keiner. Was fehlt, steht in TODO.md.
"""

from __future__ import annotations

import argparse
import sys

from . import __version__, profil, umgebung, zustand


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


def _aufraeumen() -> int:
    """Nach einem Absturz liegengebliebene Journale finden.

    Zurückgesetzt wird hier noch nichts – das kommt mit ``starten``. Melden
    tut der Befehl aber schon, damit man sieht, dass das Netz gespannt ist.
    """
    verwaist = zustand.verwaiste_journale()
    if not verwaist:
        print("Nichts aufzuräumen.")
        return 0
    for journal in verwaist:
        print(f"Verwaistes Journal: {journal.spiel} (Prozess {journal.pid} lebt nicht mehr)")
        for eintrag in journal.eintraege:
            print(f"    {eintrag.stellschraube} an {eintrag.ziel}: zurück auf {eintrag.vorher}")
    print()
    print("Zurückgesetzt wird noch nichts – siehe TODO.md.")
    return 0


def main(argv: list[str] | None = None) -> int:
    zerleger = argparse.ArgumentParser(
        prog="spielraum",
        description="Spiele starten, das System dafür herrichten, hinterher aufräumen.",
    )
    zerleger.add_argument("--version", action="version", version=f"SPIELRaum {__version__}")
    unterbefehle = zerleger.add_subparsers(dest="befehl")

    unterbefehle.add_parser("umgebung", help="Was findet SPIELRaum auf diesem Rechner vor?")
    unterbefehle.add_parser("profile", help="Welche Spielprofile sind eingerichtet?")
    spiele = unterbefehle.add_parser("spiele", help="Welche Spiele sind installiert?")
    spiele.add_argument(
        "--alle", action="store_true",
        help="auch Proton und die Steam-Laufzeiten aufführen",
    )
    pruefen = unterbefehle.add_parser("pruefen", help="Eine Profildatei auf Fehler prüfen")
    pruefen.add_argument("datei", help="Pfad oder Dateiname im Profilverzeichnis")
    unterbefehle.add_parser("aufraeumen", help="Liegengebliebene Journale suchen")

    args = zerleger.parse_args(argv)

    if args.befehl == "umgebung":
        return _umgebung_zeigen()
    if args.befehl == "profile":
        return _profile_zeigen()
    if args.befehl == "spiele":
        return _spiele_zeigen(alle=args.alle)
    if args.befehl == "pruefen":
        return _pruefen(args.datei)
    if args.befehl == "aufraeumen":
        return _aufraeumen()

    zerleger.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
