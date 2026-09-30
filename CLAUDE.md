# Hinweise für die Arbeit an SPIELRaum

## Worum es geht

Spiele starten, das System dafür herrichten, hinterher aufräumen – mit einem
Profil **pro Spiel**. Das Zurücksetzen ist die eigentliche Zusage des
Programms, nicht das Optimieren.

## Zwei Zielsysteme, von Anfang an

Arch/Manjaro **und** Debian 13. Das ist keine Absichtserklärung für später,
sondern gilt für jede Zeile:

- Nie einen Pfad oder Programmnamen fest verdrahten. Alles geht über
  `spielraum/umgebung.py`.
- Nie `ID` aus `/etc/os-release` prüfen, immer `ID_LIKE` mitnehmen. Manjaro
  meldet `manjaro`, Mint meldet `linuxmint`.
- Verzeichnisse nach XDG, nicht `~/.config` hinschreiben. Unter
  Flatpak-Steam stimmt das sonst nicht.
- Fehlt ein Werkzeug, ist das kein Absturz, sondern eine Stellschraube, die
  ausfällt – mit einer Meldung, die den Installationsbefehl der jeweiligen
  Familie nennt.

## Was nicht nachgebaut wird

GameMode macht den Teil mit Systemrechten. Er liegt in beiden
Distributionsquellen und hat einen geprüften Dienst. SPIELRaum ruft ihn auf
und legt obendrauf, was er nicht kann: Profile pro Spiel, Umgebung,
Startargumente, Spieldateien, Messung.

## Sicherheit

**Profile enthalten keine Befehle.** Kein Feld, in das eine Befehlszeile
passt, kein `eval`, kein `shell=True`. Ein Profil nennt Werte aus einer festen
Liste; das *Wie* steht im Programm. Wer diese Regel aufweicht, macht aus einer
Konfigurationsdatei einen Weg zu erhöhten Rechten.

## Zurücksetzen

Vier Netze, siehe `spielraum/zustand.py`: alter Wert vor der Änderung ins
Journal, Journal auf die Platte, atomar geschrieben, verwaiste Journale beim
nächsten Start einsammeln. Wer eine neue Stellschraube einbaut, baut den
Journaleintrag mit – nicht danach.

## Stil

Wie in den anderen Programmen: deutsche Prosa in Kommentaren, und zwar das
**Warum**, nicht das Was. Wo eine Entscheidung aus einem konkreten Vorfall
stammt, gehört der Vorfall mit Datum dazu. Doku zweisprachig, im selben Zug.

## Messen statt behaupten

Keine Optimierung ohne Messwert. Was nicht gemessen ist, steht auskommentiert
im Profil oder als offener Punkt in TODO.md – nicht als eingeschaltete
Einstellung mit einem zuversichtlichen Kommentar daneben.
