[Deutsch](README.md) | [Übersicht](../README.md) | [Änderungsprotokoll](../CHANGELOG.md) | [TODO](../TODO.md)

# Anleitungen

## Entscheidungen

- [installation.md](installation.md) – Einrichten unter Arch/Manjaro, Debian 13 und Ubuntu ([English](installation.en.md))

- [Was ein Dienst mit Systemrechten kosten würde](systemdienst.md) – warum
  SPIELRaum die Grafikkarte nicht anfasst, und ab wann sich das ändern
  sollte. Mit der Messung, die die Frage entschieden hat.

- [GameMode darf nicht immer, was es soll](gamemode.md) – auf Arch und
  Manjaro verbietet die mitgelieferte Polkit-Regel das Ändern des
  Taktreglers, auch dem angemeldeten Nutzer. Warum `install.sh` das nicht
  von sich aus geraderückt, und wie man es selbst tut.

## Benutzen

- [Was SPIELRaum misst und wie man es liest](messen.md) – die drei
  Zahlen, warum die ersten zehn Sekunden nicht zählen und wann ein
  Unterschied einer ist.

- [Die Messfahrt](messfahrt.md) – Varianten nacheinander messen, ohne dass
  jemand ins Spielmenü muss. Seit Fassung 0.6.0 gebaut; das Papier
  beschreibt den Ablauf und die Stelle, an der es schwierig wird.

- [Tastenbelegung pro Spiel](tasten.md) – über keyd, auf Zeit. Und die
  Falle, die am 23.10. und am 03.11.2026 zugebissen hat: Die Bewegung darf
  nur auf **einer** Seite umgelegt werden.

- [Den Mod Loader aktuell halten](modloader.md) – prüfen und herunterladen
  von selbst, einbauen auf Verlangen. Warum das Einbauen ein eigener
  Schritt ist.

## Noch zu schreiben

- Ein Profil von Hand anlegen
- SPIELRaum in die Steam-Startoptionen eintragen
