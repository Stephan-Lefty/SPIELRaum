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

echo "SPIELRaum einrichten"
echo "===================="
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
    if ! python3 -m venv "$UMGEBUNG" 2>/dev/null; then
        echo >&2
        echo "Fehler: Die Python-Umgebung ließ sich nicht anlegen." >&2
        if [ -f /etc/debian_version ]; then
            echo "Auf Debian/Ubuntu fehlt dafür meist ein Paket:" >&2
            echo "    sudo apt install python3-venv" >&2
        fi
        exit 1
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

echo "Starter: $ZIEL/spielraum"

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
echo "In den Steam-Startoptionen eines Spiels:"
echo
echo "    spielraum starten %command%"
