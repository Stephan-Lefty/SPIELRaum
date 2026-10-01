"""Die Startdatei eines Spiels lesen und prüfen.

Ein Profil ist eine TOML-Datei pro Spiel. TOML, weil Python es seit 3.11 mit
``tomllib`` selbst lesen kann – Debian 13 bringt Python 3.13 mit, Manjaro
ohnehin Neueres. Kein Paket nachzuziehen, nur um eine Konfigurationsdatei zu
lesen, ist an dieser Stelle mehr wert als jedes Format-Argument.

**Wichtig: Profile enthalten keine Befehle.** Es ist verlockend, ein Feld
``vorher = "..."`` einzubauen, in das man eine Befehlszeile schreibt. Das wäre
ein Einfallstor: Wer die Profildatei schreiben darf, führt sonst später Code
mit erhöhten Rechten aus. Ein Profil sagt deshalb nur *was* sein soll, aus
einer festen Liste bekannter Stellschrauben. Das *wie* steht im Programm.
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from . import umgebung

# Welche Governor-Werte sind überhaupt erlaubt? Die Liste stammt nicht aus dem
# Kopf, sondern wird beim Anwenden gegen das geprüft, was der Kernel unter
# scaling_available_governors meldet. Hier steht nur, was syntaktisch als
# Governor durchgeht – damit ein Tippfehler früh auffällt und nicht erst,
# wenn das Spiel schon läuft.
GOVERNOR_MUSTER = re.compile(r"^[a-z_]{3,20}$")

# Umgebungsvariablen: Name streng, Wert frei. Der Name landet in der Umgebung
# eines Kindprozesses; alles außer Großbuchstaben, Ziffern und Unterstrich hat
# dort nichts zu suchen.
VARIABLE_MUSTER = re.compile(r"^[A-Z_][A-Z0-9_]*$")


class ProfilFehler(Exception):
    """Das Profil ist unbrauchbar. Die Meldung sagt, welche Zeile gemeint ist."""


# Welche Dateiformate SPIELRaum anfassen kann.
#
#   godot-cfg   das INI-artige override.cfg (spielraum/godot_cfg.py)
#   godot-tres  Godot-Ressourcen wie Preferences.tres (godot_tres.py)
#
# Die Liste ist bewusst kurz. Jedes Format braucht einen eigenen Leser, der
# nur ändert, was geändert werden soll, und alles andere Zeichen für Zeichen
# durchreicht - eine Datei, die ein fremdes Programm verwaltet, baut man
# nicht neu auf.
ARTEN = ("godot-cfg", "godot-tres")


@dataclass
class Dateiaenderung:
    """Eine Datei des Spiels, die SPIELRaum anfasst – immer mit Sicherung."""

    pfad: str
    art: str
    zusammenfuehren: bool = True
    # godot-cfg: {Abschnitt: {Schlüssel: Wert}}
    # godot-tres: {Schlüssel: Wert}
    werte: dict = field(default_factory=dict)


@dataclass
class Variante:
    """Eine Richtung, zwischen denen der Anwender wählt.

    Varianten sind die Antwort auf eine Einsicht vom 01.10.2026: »Optimal«
    kann ein Programm nicht wissen, weil es Geschmack ist. Ob jemand lieber
    61 Bilder ohne Kantenglättung hat oder 41 mit - das entscheidet er.
    SPIELRaum erledigt nur die Mechanik und sagt dazu, was gemessen wurde.
    """

    name: str
    beschreibung: str = ""
    # {Dateikennung: {Schlüssel: Wert}} - die Kennung verweist auf [dateien.X]
    dateien: dict[str, dict] = field(default_factory=dict)


@dataclass
class Profil:
    """Was für ein Spiel gelten soll."""

    name: str
    quelle: Path
    steam_app_id: int | None = None
    engine: str | None = None

    gamemode: bool = True
    cpu_governor: str | None = None
    nicht_stoeren: bool = False

    variablen: dict[str, str] = field(default_factory=dict)
    argumente: list[str] = field(default_factory=list)
    dateien: dict[str, Dateiaenderung] = field(default_factory=dict)
    varianten: dict[str, Variante] = field(default_factory=dict)

    mangohud: bool = True

    def warnungen(self) -> list[str]:
        """Was am Profil zwar erlaubt, auf *diesem* Rechner aber wirkungslos ist.

        Kein Fehler – ein Profil soll auf mehreren Rechnern taugen. Aber wer
        ``gamemode = true`` schreibt und GameMode nicht installiert hat, soll
        das erfahren, bevor er sich über ausbleibende Wirkung wundert.
        """
        umg = umgebung.ermitteln()
        offen: list[str] = []
        if self.gamemode and not umg.hat("gamemoderun"):
            offen.append(umg.fehlt_hinweis("gamemoderun"))
        if self.mangohud and not umg.hat("mangohud"):
            offen.append(umg.fehlt_hinweis("mangohud"))
        return offen


def _als_str(wert: object, feld: str) -> str:
    if not isinstance(wert, str):
        raise ProfilFehler(f"»{feld}« muss Text sein, ist aber {type(wert).__name__}.")
    return wert


def laden(pfad: Path) -> Profil:
    """Eine Profildatei einlesen und auf Plausibilität prüfen."""
    try:
        roh = tomllib.loads(pfad.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ProfilFehler(f"Es gibt keine Profildatei {pfad}.") from None
    except tomllib.TOMLDecodeError as fehler:
        raise ProfilFehler(f"{pfad.name} ist kein gültiges TOML: {fehler}") from None

    spiel = roh.get("spiel")
    if not isinstance(spiel, dict) or "name" not in spiel:
        raise ProfilFehler(f"{pfad.name}: Der Abschnitt [spiel] mit »name« fehlt.")

    profil = Profil(name=_als_str(spiel["name"], "spiel.name"), quelle=pfad)

    if (app_id := spiel.get("steam_app_id")) is not None:
        if not isinstance(app_id, int) or app_id <= 0:
            raise ProfilFehler("»spiel.steam_app_id« muss eine positive Zahl sein.")
        profil.steam_app_id = app_id
    if (engine := spiel.get("engine")) is not None:
        profil.engine = _als_str(engine, "spiel.engine")

    system = roh.get("system", {})
    if not isinstance(system, dict):
        raise ProfilFehler("Der Abschnitt [system] muss eine Tabelle sein.")
    profil.gamemode = bool(system.get("gamemode", True))
    profil.nicht_stoeren = bool(system.get("nicht_stoeren", False))
    if (gov := system.get("cpu_governor")) is not None:
        gov = _als_str(gov, "system.cpu_governor")
        if not GOVERNOR_MUSTER.match(gov):
            raise ProfilFehler(f"»{gov}« sieht nicht wie ein Governor-Name aus.")
        profil.cpu_governor = gov

    for name, wert in (roh.get("umgebung") or {}).items():
        if not VARIABLE_MUSTER.match(name):
            raise ProfilFehler(
                f"»{name}« ist kein zulässiger Name für eine Umgebungsvariable."
            )
        # Zahlen und Wahrheitswerte nimmt TOML gern an; die Umgebung kennt aber
        # nur Text. Still umwandeln ist hier richtig – alles andere wäre
        # Schikane für eine Zeile wie DXVK_FRAME_RATE = 60.
        profil.variablen[name] = str(wert).lower() if isinstance(wert, bool) else str(wert)

    start = roh.get("start", {})
    if argumente := start.get("argumente"):
        if not isinstance(argumente, list) or not all(isinstance(a, str) for a in argumente):
            raise ProfilFehler("»start.argumente« muss eine Liste aus Text sein.")
        profil.argumente = list(argumente)

    for kennung, block in (roh.get("dateien") or {}).items():
        if not isinstance(block, dict) or "pfad" not in block:
            raise ProfilFehler(f"[dateien.{kennung}]: »pfad« fehlt.")
        art = _als_str(block.get("art", "godot-cfg"), f"dateien.{kennung}.art")
        if art not in ARTEN:
            raise ProfilFehler(
                f"[dateien.{kennung}]: »{art}« kennt SPIELRaum nicht. "
                "Möglich sind: " + ", ".join(ARTEN)
            )
        dateipfad = _als_str(block["pfad"], f"dateien.{kennung}.pfad")
        # Absolute Pfade sind hier verboten, und zwar aus einem konkreten
        # Grund: Wer ein Spiel deinstalliert und später neu lädt, bekommt es
        # womöglich in eine andere Bibliothek - Steam nimmt die, wo Platz ist.
        # Ein Profil mit »/mnt/HDD-1.0TB/...« zeigt dann ins Leere, im
        # schlimmsten Fall auf die Datei eines anderen Spiels. Deshalb nur
        # Platzhalter, die beim Start aufgelöst werden.
        if dateipfad.startswith("/") or dateipfad.startswith("~"):
            raise ProfilFehler(
                f"[dateien.{kennung}]: »{dateipfad}« ist ein fester Pfad. "
                "Nach einer Neuinstallation kann das Spiel woanders liegen – "
                "bitte {spielordner} oder {praefix} verwenden."
            )
        profil.dateien[kennung] = Dateiaenderung(
            pfad=dateipfad,
            art=art,
            zusammenfuehren=bool(block.get("zusammenfuehren", True)),
            werte=block.get("werte", {}),
        )

    # --- Varianten ---------------------------------------------------
    # Eine Variante nennt je Datei die Werte, die für sie gelten. Welche
    # Datei gemeint ist, steht als Kennung da und muss in [dateien] stehen -
    # geprüft wird das hier, nicht erst beim Anwenden.
    for name, block in (roh.get("varianten") or {}).items():
        if not isinstance(block, dict):
            raise ProfilFehler(f"[varianten.{name}] muss eine Tabelle sein.")
        variante = Variante(
            name=name,
            beschreibung=_als_str(block.get("beschreibung", ""),
                                  f"varianten.{name}.beschreibung"),
        )
        for schluessel, werte in block.items():
            if schluessel == "beschreibung":
                continue
            if not isinstance(werte, dict):
                raise ProfilFehler(
                    f"[varianten.{name}]: »{schluessel}« muss eine Tabelle von "
                    "Werten sein, etwa { lighting = 1 }."
                )
            if schluessel not in profil.dateien:
                raise ProfilFehler(
                    f"[varianten.{name}] verweist auf »{schluessel}«, aber es "
                    f"gibt kein [dateien.{schluessel}]. Vorhanden: "
                    + (", ".join(profil.dateien) or "nichts")
                )
            variante.dateien[schluessel] = dict(werte)
        profil.varianten[name] = variante

    messen = roh.get("messen", {})
    profil.mangohud = bool(messen.get("mangohud", True))

    return profil


def profil_verzeichnis() -> Path:
    return umgebung.konfig_verzeichnis() / "spiele"


def finden(steam_app_id: int | None = None, name: str | None = None) -> Profil | None:
    """Das passende Profil suchen.

    Die Steam-App-ID ist der verlässliche Weg: Steam setzt sie beim Start als
    Umgebungsvariable, und sie ändert sich nicht, wenn jemand das Spiel
    umbenennt oder auf eine andere Platte schiebt.
    """
    verzeichnis = profil_verzeichnis()
    if not verzeichnis.is_dir():
        return None
    for datei in sorted(verzeichnis.glob("*.toml")):
        try:
            profil = laden(datei)
        except ProfilFehler:
            # Ein kaputtes Profil darf nicht verhindern, dass die anderen
            # gefunden werden. Gemeldet wird es beim gezielten Laden.
            continue
        if steam_app_id is not None and profil.steam_app_id == steam_app_id:
            return profil
        if name is not None and profil.name.casefold() == name.casefold():
            return profil
    return None
