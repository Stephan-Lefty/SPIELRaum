#!/usr/bin/env bash
# SPIELRaum einrichten - für Arch/Manjaro und Debian 13.
#
# Legt eine eigene Python-Umgebung im Repository an, installiert SPIELRaum
# hinein und stellt einen Starter nach ~/.local/bin. Nichts davon braucht
# Systemrechte, und nichts landet außerhalb von $HOME.
#
# Warum ein Starter und kein Verweis auf die Umgebung: Der Pfad zum
# Repository kann Leerzeichen enthalten - bei der Entwicklung war das der
# Fall ("eigene Daten"). In den Steam-Startoptionen ist ein Pfad mit
# Leerzeichen eine Fehlerquelle, die niemand sucht. ~/.local/bin/spielraum
# hat keine.

set -euo pipefail

HIER="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ZIEL="$HOME/.local/bin"
UMGEBUNG="$HIER/.venv"

AUTOMATISCH=0
for arg in "$@"; do
    case "$arg" in
        --ja|-j) AUTOMATISCH=1 ;;
        --hilfe|-h|--help)
            echo "Aufruf: ./install.sh [--ja]"
            echo
            echo "  --ja   Fehlende Pakete ohne Rückfrage nachinstallieren."
            exit 0 ;;
    esac
done

echo "SPIELRaum einrichten"
echo "===================="
echo

# --- Welche Familie? -------------------------------------------------------
# ID_LIKE ist hier wichtiger als ID: Manjaro meldet »manjaro« mit
# ID_LIKE=arch, Mint meldet »linuxmint« mit ID_LIKE="ubuntu debian". Wer nur
# ID prüft, unterstützt zwei Distributionen statt zweier Familien.
FAMILIE="unbekannt"
if [ -r /etc/os-release ]; then
    # shellcheck disable=SC1091
    . /etc/os-release
    case " ${ID:-} ${ID_LIKE:-} " in
        *" arch "*|*" archlinux "*|*" manjaro "*) FAMILIE="arch" ;;
        *" debian "*|*" ubuntu "*)                FAMILIE="debian" ;;
    esac
fi

# --- Gibt es dieses Paket überhaupt? ---------------------------------------
# Auf Debian ist der Name von PySide6 nicht überall derselbe. Statt einen
# zu raten und am Nutzer scheitern zu lassen, werden mehrere Kandidaten
# geprüft und der erste genommen, den die Quellen kennen.
paket_gibt_es() {
    case "$FAMILIE" in
        arch)   pacman -Si "$1" >/dev/null 2>&1 ;;
        debian) apt-cache show "$1" >/dev/null 2>&1 ;;
        *)      return 1 ;;
    esac
}

erster_kandidat() {
    for kandidat in "$@"; do
        if paket_gibt_es "$kandidat"; then
            echo "$kandidat"
            return 0
        fi
    done
    return 1
}

FEHLT=()
notieren() {
    # $1 = Prüfbefehl, $2.. = Paketkandidaten
    local pruefung="$1"; shift
    eval "$pruefung" >/dev/null 2>&1 && return 0
    local paket
    if paket="$(erster_kandidat "$@")"; then
        FEHLT+=("$paket")
    else
        echo "  Hinweis: Für »$1« ist in den Quellen kein Paket zu finden."
        echo "           Gesucht wurde nach: $*"
    fi
}

echo "Sehe nach, was fehlt ..."
if [ "$FAMILIE" = "arch" ]; then
    notieren "command -v git"       git
    notieren "python3 -c 'import venv'" python
    notieren "python3 -c 'import PySide6.QtWidgets'" pyside6
    notieren "command -v gamemoderun" gamemode
    notieren "command -v mangohud"  mangohud
    notieren "command -v keyd"      keyd
elif [ "$FAMILIE" = "debian" ]; then
    notieren "command -v git"       git
    notieren "python3 -c 'import venv'" python3-venv
    # Debian schnürt PySide6 in Teilpakete, und die Namen haben sich
    # zwischen den Fassungen geändert. Der erste Treffer gewinnt.
    notieren "python3 -c 'import PySide6.QtWidgets'" \
        python3-pyside6.qtwidgets python3-pyside6 pyside6-tools
    notieren "command -v gamemoderun" gamemode
    notieren "command -v mangohud"  mangohud
    notieren "command -v keyd"      keyd
else
    echo "  Unbekannte Distribution – es wird nichts nachinstalliert."
    echo "  Gebraucht werden: python3 (3.11+), python3-venv, PySide6,"
    echo "  dazu freiwillig gamemode, mangohud, keyd."
fi

if [ ${#FEHLT[@]} -gt 0 ]; then
    echo
    echo "Es fehlen: ${FEHLT[*]}"
    if [ "$FAMILIE" = "arch" ]; then
        BEFEHL=(sudo pacman -S --needed "${FEHLT[@]}")
    else
        BEFEHL=(sudo apt install -y "${FEHLT[@]}")
    fi
    echo "Befehl:    ${BEFEHL[*]}"
    echo
    if [ "$AUTOMATISCH" -eq 1 ]; then
        ANTWORT="j"
    else
        # Beim Nachinstallieren wird zum ersten Mal nach dem Passwort
        # gefragt. Wer das nicht erwartet, soll Nein sagen können.
        printf "Jetzt nachinstallieren? [j/N] "
        read -r ANTWORT </dev/tty || ANTWORT="n"
    fi
    case "$ANTWORT" in
        [jJyY]*)
            "${BEFEHL[@]}" || {
                echo "Das Nachinstallieren ist fehlgeschlagen." >&2
                echo "SPIELRaum läuft trotzdem – es fallen nur die" >&2
                echo "betroffenen Stellschrauben aus." >&2
            } ;;
        *) echo "Übersprungen. Fehlende Werkzeuge fallen aus, mehr nicht." ;;
    esac
else
    echo "  Alles da."
fi
echo

# --- Python prüfen ---------------------------------------------------------
# 3.11 ist die Untergrenze: tomllib kam damit in die Standardbibliothek.
if ! command -v python3 >/dev/null; then
    echo "Fehler: python3 ist nicht installiert." >&2
    exit 1
fi

python3 - <<'PY' || exit 1
import sys
if sys.version_info < (3, 11):
    print(f"Fehler: Python {sys.version_info.major}.{sys.version_info.minor} "
          "ist zu alt. SPIELRaum braucht 3.11 oder neuer.")
    sys.exit(1)
PY

echo "Python: $(python3 --version)"

# --- Die eigene Umgebung ---------------------------------------------------
# Auf Debian steckt venv in einem eigenen Paket und fehlt oft. Die Meldung
# von Python dazu ist wenig hilfreich, deshalb hier eine eigene.
if [ ! -d "$UMGEBUNG" ]; then
    echo "Lege Python-Umgebung an ..."
    # --system-site-packages, damit PySide6 aus der Distribution
    # sichtbar ist. Ueber pip nachgezogen braechte es sein eigenes Qt
    # mit - 150 MB, die sich mit dem System beissen koennen.
    if ! python3 -m venv --system-site-packages "$UMGEBUNG" 2>/dev/null; then
        echo >&2
        echo "Fehler: Die Python-Umgebung ließ sich nicht anlegen." >&2
        if [ -f /etc/debian_version ]; then
            echo "Auf Debian/Ubuntu fehlt dafür meist ein Paket:" >&2
            echo "    sudo apt install python3-venv" >&2
        fi
        exit 1
    fi
else
    # Eine Umgebung aus einer frueheren Fassung sieht die Pakete des
    # Systems nicht - und damit kein PySide6. Statt sie wegzuwerfen,
    # wird der Schalter in pyvenv.cfg umgelegt; das ist genau die
    # Stelle, die "python3 -m venv --system-site-packages" schreibt.
    KONFIG="$UMGEBUNG/pyvenv.cfg"
    if [ -f "$KONFIG" ] && grep -q "include-system-site-packages *= *false" "$KONFIG"; then
        echo "Schalte vorhandene Umgebung auf die Pakete des Systems um ..."
        sed -i "s/include-system-site-packages *= *false/include-system-site-packages = true/" "$KONFIG"
    fi
fi

echo "Installiere SPIELRaum ..."
"$UMGEBUNG/bin/pip" install --quiet --upgrade pip
"$UMGEBUNG/bin/pip" install --quiet -e "$HIER"

# --- Der Starter -----------------------------------------------------------
mkdir -p "$ZIEL"
cat > "$ZIEL/spielraum" <<STARTER
#!/bin/sh
# Erzeugt von install.sh. Nicht von Hand ändern - beim nächsten Lauf
# wird die Datei überschrieben.
exec "$UMGEBUNG/bin/python3" -m spielraum.cli "\$@"
STARTER
chmod +x "$ZIEL/spielraum"

cat > "$ZIEL/spielraum-ui" <<STARTER
#!/bin/sh
# Erzeugt von install.sh. Nicht von Hand aendern.
exec "$UMGEBUNG/bin/python3" -m spielraum.ui.fenster "\$@"
STARTER
chmod +x "$ZIEL/spielraum-ui"

echo "Starter: $ZIEL/spielraum und $ZIEL/spielraum-ui"

# --- Eintrag im Anwendungsmenue -------------------------------------------
# Nach XDG, nicht nach /usr/share - das braeuchte Systemrechte, und die
# will dieses Skript nicht.
MENUE="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
SYMBOLE="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor"
mkdir -p "$MENUE"
for groesse in 16 24 32 48 64 128 256 512; do
    if [ -f "$HIER/assets/icon-$groesse.png" ]; then
        mkdir -p "$SYMBOLE/${groesse}x${groesse}/apps"
        cp "$HIER/assets/icon-$groesse.png" "$SYMBOLE/${groesse}x${groesse}/apps/spielraum.png"
    fi
done
cat > "$MENUE/spielraum.desktop" <<EINTRAG
[Desktop Entry]
Type=Application
Name=SPIELRaum
Comment=Spiele starten, das System dafuer herrichten, hinterher aufraeumen
Comment[en]=Start a game, set the machine up for it, clean up afterwards
Exec=$ZIEL/spielraum-ui
Icon=spielraum
Terminal=false
Categories=Game;Settings;
Keywords=Spiel;Gaming;Steam;Proton;
EINTRAG
command -v update-desktop-database >/dev/null && \
    update-desktop-database "$MENUE" 2>/dev/null || true
echo "Menue:   $MENUE/spielraum.desktop"

# --- Profile mitgeben ------------------------------------------------------
PROFILE="${XDG_CONFIG_HOME:-$HOME/.config}/spielraum/spiele"
mkdir -p "$PROFILE"
NEU=0
for datei in "$HIER"/profile/*.toml; do
    [ -e "$datei" ] || continue
    if [ ! -e "$PROFILE/$(basename "$datei")" ]; then
        cp "$datei" "$PROFILE/"
        NEU=$((NEU + 1))
    fi
done
# Vorhandene Profile werden nicht angefasst. Wer eines angepasst hat, will
# es nicht bei der nächsten Einrichtung überschrieben bekommen.
[ "$NEU" -gt 0 ] && echo "Profile:  $NEU neu nach $PROFILE kopiert"

# --- Nachsehen, ob der Starter auch gefunden wird ---------------------------
echo
case ":$PATH:" in
    *":$ZIEL:"*)
        echo "Fertig. Zum Ausprobieren:"
        echo
        echo "    spielraum spiele"
        ;;
    *)
        echo "Fertig - aber $ZIEL liegt nicht im PATH."
        echo "Diese Zeile gehört in ~/.bashrc oder ~/.zshrc:"
        echo
        echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
        ;;
esac

echo
if "$UMGEBUNG/bin/python3" -c "import PySide6" 2>/dev/null; then
    echo "Oberflaeche:  spielraum-ui"
else
    if [ -f /etc/debian_version ]; then
        echo "Fuer die Oberflaeche fehlt noch PySide6:"
        echo "    sudo apt install python3-pyside6.qtwidgets"
    else
        echo "Fuer die Oberflaeche fehlt noch PySide6:"
        echo "    sudo pacman -S pyside6"
    fi
fi
echo
echo "In den Steam-Startoptionen eines Spiels:"
echo
echo "    spielraum starten %command%"
