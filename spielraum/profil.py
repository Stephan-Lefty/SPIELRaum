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

# Wo MangoHud sein Overlay zeichnet. Die Liste stammt nicht aus dem
# Gedächtnis, sondern aus der Bibliothek selbst (`strings libMangoHud.so`).
# Wie viel von der Anzeige im Bild steht.
#
# »aus« ist kein Schönheitswert, sondern schaltet die MESSUNG mit ab --
# belegt am 12.11.2026 mit vkcube, zwei Durchgänge je Einstellung:
#
#   voll ............ 55 Zeilen protokolliert
#   nur Bilder/s .... 55 bis 60 Zeilen
#   aus ............. 0 Zeilen
#
# MangoHuds ``no_display`` hält also nicht nur die Anzeige an, sondern auch
# das Mitschreiben. Deshalb steht die Folge in der Oberfläche direkt im
# Auswahltext und nicht in einer Fußnote: Wer sie wegklickt, hat hinterher
# keine Messung und erfährt es nie.
#
# »fahrt« ist der Ausweg aus diesem Widerspruch, vorgeschlagen am
# 12.11.2026: beim gewöhnlichen Spielen unsichtbar, während einer Messfahrt
# vollständig -- und gemessen wird in beiden Fällen.
#
# Das geht, weil MangoHud zwei verschiedene Dinge kennt, die beide wie
# »aus« aussehen:
#
#   no_display                      hält Anzeige UND Mitschreiben an
#   alpha=0, background_alpha=0     zeichnet weiter, nur durchsichtig --
#                                   und protokolliert dabei: 60 Zeilen in
#                                   derselben Probe gegen null
#
# Ob dabei wirklich nichts mehr zu sehen ist, ist NICHT geprüft: MangoHud
# umrandet seine Schrift von sich aus (``text_outline`` steht in seiner
# Beispielkonfiguration unkommentiert), und ob diese Umrandung die
# Durchsichtigkeit mitmacht, ließ sich hier nicht nachstellen.
# ``text_outline=0`` steht deshalb mit dabei. Ein Blick ins Spiel weiß
# mehr als jede Vermutung -- siehe den Fehler mit den Tastenkürzeln vom
# selben Tag.
OVERLAY_UMFAENGE = ("voll", "klein", "fahrt", "aus")

OVERLAY_ECKEN = (
    "top-left", "top-right", "middle-left", "middle-right",
    "bottom-left", "bottom-right",
)


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
    # Wo das Overlay im Bild sitzt. MangoHud kennt sechs Stellen; die
    # Vorgabe oben links deckt sich bei manchen Spielen mit deren eigener
    # Anzeige.
    overlay_ecke: str = "top-left"
    # Wie deckend der Kasten hinter der Anzeige ist, 0,0 bis 1,0.
    #
    # MangoHuds eigene Vorgabe ist 0,5 und steht damit als halbdeckender
    # Balken im Bild. Bei Road to Vostok verdeckte das am 12.11.2026 die
    # linke obere Ecke so weit, dass man das Spiel darunter nicht mehr sah.
    # 0,25 lässt die Zahlen lesbar und das Spiel sichtbar.
    #
    # Null ist erlaubt: Dann steht die Schrift ohne Kasten im Bild. Lesbar
    # bleibt sie, weil MangoHud die Buchstaben umrandet.
    overlay_deckkraft: float = 0.25
    # Wie viel angezeigt wird: alles, nur die Bildrate, nur während einer
    # Messfahrt, oder nichts. Siehe OVERLAY_UMFAENGE -- »aus« schaltet auch
    # die Messung ab, »fahrt« nicht.
    overlay_umfang: str = "voll"

    # Von selbst eine Messfahrt beginnen, wenn für dieses Spiel noch keine
    # läuft und noch keine abgeschlossen ist.
    #
    # Vorgabe aus, und das mit Bedacht: Eine Messfahrt verstellt die
    # Grafikeinstellungen. Wer sich abends hinsetzt und spielen will, soll
    # nicht plötzlich »Optik« vorfinden, ohne es angefordert zu haben. Wer
    # es trotzdem will, schaltet es hier ein -- pro Spiel.
    fahrt_automatisch: bool = False
    # Welche Varianten die Messfahrt nimmt. Leer heißt: alle. Jede kostet
    # zehn Minuten Spielzeit, und wer vier davon vergleicht, ist eine
    # Dreiviertelstunde beschäftigt -- oft genügen die beiden Enden.
    fahrt_varianten: list[str] = field(default_factory=list)

    # Welche Taste der Spieltastatur welche Taste schicken soll, solange
    # dieses Spiel läuft. Links steht, was man drückt, rechts, was das Spiel
    # sehen soll: ``up = "w"``. Die Namen prüft spielraum/tasten.py gegen
    # das, was keyd selbst als gültig ausgibt.
    tasten: dict[str, str] = field(default_factory=dict)

    # Kennung einer Mod-Loader-Quelle aus ``modloader.QUELLEN`` – oder leer.
    #
    # Hier steht bewusst **keine Adresse**, sondern nur ein Name aus einer
    # festen Liste im Programm. Eine Profildatei kann jeder bearbeiten; stünde
    # dort eine URL, aus der SPIELRaum eine Datei ins Spielverzeichnis lädt,
    # wäre das ein Weg hinein. Dieselbe Überlegung wie bei [tasten].
    #
    # Leer heißt aus. Vorgabe aus, weil SPIELRaum sonst nirgends ins Netz
    # greift – und wer das nicht erwartet, soll es nicht ungefragt bekommen.
    modloader: str = ""

    def mess_varianten(self) -> list[str]:
        """Welche Varianten eine Messfahrt misst.

        Die **eine** Antwort auf diese Frage. Vorher stand sie an drei
        Stellen verschieden: ``starten.py`` wertete ``fahrt_varianten`` aus,
        ``cli.py --starten`` und die Oberfläche nahmen stur alle Varianten.
        Folge am 05.11.2026: Eine von Hand begonnene Fahrt kündigte vier
        Läufe zu je zehn Minuten an, obwohl im Profil zwei standen – vierzig
        Minuten Spielzeit statt zwanzig, ohne dass jemand danach gefragt
        hätte. Im Änderungsprotokoll zu 0.6.1 steht die Einschränkung ohne
        Vorbehalt; sie galt nur auf einem von drei Wegen.

        Leere oder unbekannte Namen fallen heraus; bleibt nichts übrig,
        gelten alle Varianten. Ein Tippfehler soll die Fahrt nicht
        verhindern – er steht als Hinweis in ``warnungen()``.
        """
        gewaehlt = [n for n in self.fahrt_varianten if n in self.varianten]
        return gewaehlt or list(self.varianten)

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
        if self.tasten and not umg.hat("keyd"):
            offen.append(umg.fehlt_hinweis("keyd"))
        unbekannt = [n for n in self.fahrt_varianten if n not in self.varianten]
        if unbekannt:
            offen.append(
                f"»messen.fahrt_varianten« nennt {', '.join(unbekannt)} – "
                f"vorhanden sind: {', '.join(self.varianten) or 'keine'}")
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
    profil.fahrt_automatisch = bool(messen.get("fahrt", False))
    rohe_auswahl = messen.get("fahrt_varianten", [])
    if not isinstance(rohe_auswahl, list):
        raise ProfilFehler("»messen.fahrt_varianten« muss eine Liste sein.")
    profil.fahrt_varianten = [_als_str(n, "messen.fahrt_varianten") for n in rohe_auswahl]
    if (ecke := messen.get("ecke")) is not None:
        ecke = _als_str(ecke, "messen.ecke")
        if ecke not in OVERLAY_ECKEN:
            raise ProfilFehler(
                f"»{ecke}« ist keine Stelle, die MangoHud kennt. Möglich: "
                + ", ".join(OVERLAY_ECKEN)
            )
        profil.overlay_ecke = ecke
    if (deckkraft := messen.get("deckkraft")) is not None:
        # Bewusst auch int annehmen: »deckkraft = 0« ist in TOML ein
        # Ganzzahlwert, und daran soll kein Profil scheitern.
        if isinstance(deckkraft, bool) or not isinstance(deckkraft, (int, float)):
            raise ProfilFehler(
                "»messen.deckkraft« muss eine Zahl zwischen 0 und 1 sein.")
        if not 0.0 <= float(deckkraft) <= 1.0:
            raise ProfilFehler(
                f"»messen.deckkraft« liegt bei {deckkraft}; möglich ist 0 "
                f"(durchsichtig) bis 1 (deckend).")
        profil.overlay_deckkraft = float(deckkraft)
    if (umfang := messen.get("umfang")) is not None:
        umfang = _als_str(umfang, "messen.umfang")
        if umfang not in OVERLAY_UMFAENGE:
            raise ProfilFehler(
                f"»{umfang}« ist kein Umfang für die Anzeige. Möglich: "
                + ", ".join(OVERLAY_UMFAENGE)
            )
        profil.overlay_umfang = umfang

    # [tasten] -- was die Spieltastatur schicken soll, solange dieses Spiel
    # läuft. Hier wird nur die Form geprüft (Text auf Text). Ob die Namen
    # Tasten sind, weiß erst keyd; das prüft spielraum/tasten.py vor dem
    # Setzen gegen dessen eigene Liste. Eine zweite Liste hier im Profil
    # würde bei jeder keyd-Fassung veralten.
    tasten = roh.get("tasten", {})
    if not isinstance(tasten, dict):
        raise ProfilFehler("Der Abschnitt [tasten] muss eine Tabelle sein.")
    for taste, ziel in tasten.items():
        profil.tasten[taste] = _als_str(ziel, f"tasten.{taste}")

    # [modloader] quelle = "vostok"
    #
    # Geprüft wird hier gegen die feste Liste im Programm, nicht erst beim
    # Herunterladen: Ein Tippfehler soll auffallen, wenn man das Profil
    # prüft, nicht erst in dem Moment, in dem etwas aus dem Netz käme.
    ladeblock = roh.get("modloader", {})
    if not isinstance(ladeblock, dict):
        raise ProfilFehler("Der Abschnitt [modloader] muss eine Tabelle sein.")
    if quelle := ladeblock.get("quelle"):
        from . import modloader as modloader_modul

        kennung = _als_str(quelle, "modloader.quelle")
        if kennung not in modloader_modul.QUELLEN:
            raise ProfilFehler(
                f"[modloader]: »{kennung}« kennt SPIELRaum nicht. Vorhanden: "
                + ", ".join(sorted(modloader_modul.QUELLEN))
            )
        profil.modloader = kennung

    return profil


def ecke_setzen(pfad: Path, ecke: str) -> str:
    """``messen.ecke`` in einer Profildatei ändern und den alten Wert melden.

    **Warum von Hand im Text und nicht über einen TOML-Schreiber.** Die
    Profile dieses Projekts bestehen zu neun Zehnteln aus Kommentaren -- das
    Vostok-Profil hat über dreihundert Zeilen Begründung zu knapp dreißig
    Zeilen Werten. Kein TOML-Schreiber in der Standardbibliothek erhält
    Kommentare; ``tomllib`` kann ohnehin nur lesen. Wer hier neu serialisiert,
    löscht die Begründungen und merkt es nicht, weil die Datei danach gültig
    aussieht -- dieselbe Falle wie bei der Vollsicherung am 03.11.2026.

    Deshalb wird genau eine Zeile angefasst. Drei Fälle:

    * ``ecke = "..."`` steht schon da -> Wert ersetzen, Kommentar daneben
      bleibt stehen.
    * ``[messen]`` gibt es, ``ecke`` nicht -> Zeile direkt unter die
      Abschnittsüberschrift.
    * ``[messen]`` gibt es nicht -> Abschnitt am Ende anlegen.

    Gibt den vorherigen Wert zurück, oder ``""``, wenn keiner dastand.
    Geschrieben wird atomar; ein halb geschriebenes Profil wäre schlimmer
    als keines, weil SPIELRaum es beim nächsten Start nicht mehr lädt.
    """
    if ecke not in OVERLAY_ECKEN:
        raise ProfilFehler(
            f"»{ecke}« ist keine Stelle, die MangoHud kennt. Möglich: "
            + ", ".join(OVERLAY_ECKEN)
        )
    return _wert_setzen(pfad, "ecke", ecke)


def umfang_setzen(pfad: Path, umfang: str) -> str:
    """``messen.umfang`` ändern. Siehe ``ecke_setzen`` für das Verfahren.

    Erinnerung an die Folge: ``"aus"`` hält auch das Mitschreiben an, siehe
    ``OVERLAY_UMFAENGE``. Diese Funktion warnt nicht davor -- sie schreibt
    nur, was ihr gesagt wird. Gewarnt wird dort, wo gewählt wird.
    """
    if umfang not in OVERLAY_UMFAENGE:
        raise ProfilFehler(
            f"»{umfang}« ist kein Umfang für die Anzeige. Möglich: "
            + ", ".join(OVERLAY_UMFAENGE)
        )
    return _wert_setzen(pfad, "umfang", umfang)


def _wert_setzen(pfad: Path, schluessel: str, wert: str) -> str:
    """Einen Textwert im Abschnitt ``[messen]`` ändern, Kommentare erhalten.

    Der Prüfteil steht beim jeweiligen Aufrufer: Hier soll nicht eine
    wachsende Liste von Schlüsseln mit ihren erlaubten Werten entstehen.
    """
    # ``newline=""`` ist hier Bedingung, nicht Vorsicht: ``read_text``
    # wandelt CRLF beim LESEN in LF, und dann steht in ``text`` nie ein
    # ``\r`` -- die Erkennung darunter liefe immer auf LF, und die Datei
    # käme mit gewandelten Zeilenenden zurück. Am 09.11.2026 hat genau das
    # an Enshroudeds Einstellungsdatei 68 CRLF zerstört; damals beim
    # Schreiben, hier beim Lesen. Der Test test_crlf_bleibt_crlf hält es.
    with pfad.open(encoding="utf-8", newline="") as datei:
        text = datei.read()
    umbruch = "\r\n" if "\r\n" in text else "\n"
    zeilen = text.split(umbruch)

    in_messen = False
    messen_zeile = None
    for nummer, zeile in enumerate(zeilen):
        blank = zeile.strip()
        if blank.startswith("[") and blank.endswith("]"):
            in_messen = blank == "[messen]"
            if in_messen:
                messen_zeile = nummer
            continue
        if not in_messen or not blank or blank.startswith("#"):
            continue
        gefunden = blank.split("=", 1)[0].strip()
        if gefunden == schluessel:
            # Nur den Wert tauschen, alles rechts davon bleibt -- auch ein
            # Kommentar am Zeilenende.
            vorne, _, hinten = zeile.partition("=")
            rest = hinten.split("#", 1)
            kommentar = f"  #{rest[1]}" if len(rest) > 1 else ""
            # Erst den Kommentar abschneiden, DANN die Anführungszeichen.
            # Umgekehrt stand im Rückgabewert einmal
            # »top-left"  # und ein Kommentar am Zeilenende« -- ein
            # .strip('"') an einer Zeichenkette, die hinten keines mehr hat,
            # weil der Kommentar dahinter steht.
            vorher = rest[0].strip().strip('"').strip("'")
            zeilen[nummer] = f'{vorne}= "{wert}"{kommentar}'
            _atomar(pfad, umbruch.join(zeilen))
            return vorher

    neue_zeile = f'{schluessel} = "{wert}"'
    if messen_zeile is not None:
        zeilen.insert(messen_zeile + 1, neue_zeile)
    else:
        # Leerzeile davor, damit der Abschnitt nicht an den letzten Wert
        # klebt. Dass sie von uns stammt, ist hier unkritisch -- anders als
        # bei den Spieldateien nimmt niemand diese Änderung zurück.
        if zeilen and zeilen[-1].strip():
            zeilen.append("")
        zeilen.extend(["[messen]", neue_zeile])
    _atomar(pfad, umbruch.join(zeilen))
    return ""


def _atomar(ziel: Path, text: str) -> None:
    """Daneben schreiben, dann umbenennen -- wie überall in diesem Programm.

    Nicht ``stellschrauben.atomar_schreiben`` aufgerufen, obwohl es dasselbe
    tut: ``stellschrauben`` lädt ``profil``, und umgekehrt gäbe das einen
    Ringschluss beim Importieren.
    """
    import os
    import tempfile

    griff, zwischendatei = tempfile.mkstemp(dir=ziel.parent, suffix=".tmp")
    try:
        with os.fdopen(griff, "w", encoding="utf-8", newline="") as datei:
            datei.write(text)
            datei.flush()
            os.fsync(datei.fileno())
        os.replace(zwischendatei, ziel)
    except BaseException:
        Path(zwischendatei).unlink(missing_ok=True)
        raise


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
