"""Installierte Steam-Spiele finden – ohne Steam zu fragen.

SPIELRaum liest die Dateien, die Steam ohnehin auf die Platte schreibt. Das
hat zwei Gründe: Es braucht kein laufendes Steam, und es braucht keinen
Zugang zum Steam-Konto. Wer ein Spiel optimieren will, soll dafür nicht erst
irgendwo Zugangsdaten hinterlegen müssen.

Gelesen werden zwei Sorten Datei, beide im VDF-Format:

    libraryfolders.vdf      wo die Bibliotheken liegen
    appmanifest_<id>.acf    was in einer Bibliothek installiert ist

Das VDF-Format ist Valves eigenes und sieht so aus::

    "libraryfolders"
    {
        "0"
        {
            "path"    "/mnt/Gaming/SteamLibrary"
        }
    }

Es gibt Bibliotheken dafür. Hier steht trotzdem ein eigener Leser, weil er
dreißig Zeilen braucht und SPIELRaum sonst eine Abhängigkeit hätte, die in
Debian und Arch verschieden heißt oder fehlt – für ein Format, das aus
Anführungszeichen und geschweiften Klammern besteht.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# Was in einer Steam-Bibliothek liegt, aber kein Spiel ist. Ohne diese Liste
# bietet SPIELRaum dem Anwender »Proton 9.0« und »Steam Linux Runtime 3.0«
# zum Optimieren an - auf dem Rechner, auf dem das hier entstand, waren das
# acht von dreizehn Einträgen.
KEINE_SPIELE = re.compile(
    r"^(Proton|Steam Linux Runtime|Steamworks|Steam Controller|SteamVR|"
    r".*\bRuntime\b|Proton EasyAntiCheat)",
    re.IGNORECASE,
)

ZEILE = re.compile(r'"([^"]+)"\s*"([^"]*)"')
SCHLUESSEL = re.compile(r'^\s*"([^"]+)"\s*$')


def vdf_lesen(text: str) -> dict:
    """Ein VDF in verschachtelte Wörterbücher übersetzen.

    Bewusst nachsichtig: Was nicht wie ein Schlüssel-Wert-Paar oder eine
    Klammer aussieht, wird übersprungen. Steam schreibt diese Dateien selbst,
    aber sie werden auch von Werkzeugen Dritter angefasst, und ein Spielstarter
    hat kein Recht, wegen einer unerwarteten Zeile stehenzubleiben.
    """
    wurzel: dict = {}
    stapel: list[dict] = [wurzel]
    wartender_schluessel: str | None = None

    for zeile in text.splitlines():
        blank = zeile.strip()
        if not blank or blank.startswith("//"):
            continue

        if blank == "{":
            # Die Klammer gehört zum Schlüssel aus der Zeile davor.
            neu: dict = {}
            if wartender_schluessel is not None:
                stapel[-1][wartender_schluessel] = neu
                wartender_schluessel = None
            stapel.append(neu)
            continue

        if blank == "}":
            if len(stapel) > 1:
                stapel.pop()
            continue

        if treffer := ZEILE.match(blank):
            stapel[-1][treffer.group(1)] = treffer.group(2)
            wartender_schluessel = None
            continue

        if treffer := SCHLUESSEL.match(blank):
            wartender_schluessel = treffer.group(1)

    return wurzel


@dataclass
class Spiel:
    """Ein installiertes Spiel, so wie es auf der Platte liegt."""

    app_id: int
    name: str
    ordner: Path
    groesse: int  # Bytes laut Steam
    bibliothek: Path
    proton_praefix: Path | None = None

    @property
    def laeuft_unter_proton(self) -> bool:
        """Gibt es ein Proton-Präfix, ist es ein Windows-Spiel unter Proton."""
        return self.proton_praefix is not None

    @property
    def groesse_lesbar(self) -> str:
        wert = float(self.groesse)
        for einheit in ("B", "KB", "MB", "GB"):
            if wert < 1024 or einheit == "GB":
                return f"{wert:.1f} {einheit}".replace(".", ",")
            wert /= 1024
        return f"{wert:.1f} GB"


def steam_wurzeln() -> list[Path]:
    """Wo Steam selbst installiert sein könnte.

    Vier Pfade, weil es vier gibt: der klassische, der nach XDG, der von
    Flatpak und der von Snap. Auf Debian ist Flatpak-Steam verbreiteter als
    auf Arch – wer nur ``~/.steam`` prüft, findet dort gar nichts.
    """
    heim = Path.home()
    return [
        heim / ".steam" / "steam",
        heim / ".local" / "share" / "Steam",
        heim / ".var" / "app" / "com.valvesoftware.Steam" / "data" / "Steam",
        heim / "snap" / "steam" / "common" / ".local" / "share" / "Steam",
    ]


def bibliotheken() -> list[Path]:
    """Alle Steam-Bibliotheken, auch die auf anderen Platten.

    Die Liste steht in ``libraryfolders.vdf``. Sie hat über die Jahre zwei
    Formen gehabt: früher direkt ``"1" "/pfad"``, heute ein Block mit
    ``"path"``. Beide werden hier gelesen, weil alte Installationen die alte
    Form behalten.
    """
    gefunden: list[Path] = []

    for wurzel in steam_wurzeln():
        if not wurzel.is_dir():
            continue
        # Die eigene Bibliothek zählt mit, sie steht nicht immer in der Liste.
        if (wurzel / "steamapps").is_dir():
            gefunden.append(wurzel / "steamapps")

        for kandidat in (wurzel / "steamapps" / "libraryfolders.vdf",
                         wurzel / "config" / "libraryfolders.vdf"):
            if not kandidat.is_file():
                continue
            try:
                daten = vdf_lesen(kandidat.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                continue
            for eintrag in (daten.get("libraryfolders") or {}).values():
                pfad = eintrag.get("path") if isinstance(eintrag, dict) else eintrag
                if not isinstance(pfad, str):
                    continue
                steamapps = Path(pfad) / "steamapps"
                if steamapps.is_dir():
                    gefunden.append(steamapps)

    # Zweimal dieselbe Bibliothek ist möglich: ~/.steam/steam ist oft ein
    # Verweis auf ~/.local/share/Steam. Auflösen und eindeutig machen.
    eindeutig: dict[Path, None] = {}
    for pfad in gefunden:
        eindeutig.setdefault(pfad.resolve(), None)
    return list(eindeutig)


def spiele_finden(mit_werkzeugen: bool = False) -> list[Spiel]:
    """Alle installierten Spiele über alle Bibliotheken hinweg.

    ``mit_werkzeugen`` nimmt Proton und die Steam-Laufzeiten mit auf. Das ist
    zum Nachsehen gelegentlich nützlich, zum Auswählen nie.
    """
    gefunden: list[Spiel] = []
    gesehen: set[int] = set()

    for steamapps in bibliotheken():
        for manifest in sorted(steamapps.glob("appmanifest_*.acf")):
            try:
                daten = vdf_lesen(manifest.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                continue
            zustand = daten.get("AppState")
            if not isinstance(zustand, dict):
                continue

            try:
                app_id = int(zustand.get("appid", 0))
            except ValueError:
                continue
            name = zustand.get("name", "").strip()
            ordnername = zustand.get("installdir", "").strip()
            if not app_id or not name or not ordnername or app_id in gesehen:
                continue
            if not mit_werkzeugen and KEINE_SPIELE.match(name):
                continue

            ordner = steamapps / "common" / ordnername
            if not ordner.is_dir():
                # Im Manifest steht es, auf der Platte fehlt es - etwa weil
                # eine externe Platte gerade nicht eingehängt ist.
                continue

            try:
                groesse = int(zustand.get("SizeOnDisk", 0))
            except ValueError:
                groesse = 0

            praefix = steamapps / "compatdata" / str(app_id)
            gesehen.add(app_id)
            gefunden.append(
                Spiel(
                    app_id=app_id,
                    name=name,
                    ordner=ordner,
                    groesse=groesse,
                    bibliothek=steamapps,
                    proton_praefix=praefix if praefix.is_dir() else None,
                )
            )

    return sorted(gefunden, key=lambda s: s.name.casefold())
