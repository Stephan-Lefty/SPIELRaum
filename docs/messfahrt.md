[Deutsch](messfahrt.md) | [Anleitungen](README.md) | [Übersicht](../README.md)

# Die Messfahrt

*Entwurf vom 01.10.2026. Noch nicht gebaut – dieses Papier beschreibt, was
gebaut werden soll und woran es hängt.*

## Wozu

Heute geht das Vergleichen von Einstellungen so: ins Spielmenü, umstellen,
spielen, beenden, Zahlen ansehen, wieder ins Menü. Sechsmal hintereinander,
und wer sich verzählt, vergleicht hinterher Äpfel mit Birnen.

Die Messfahrt nimmt einem alles ab außer dem Spielen selbst:

    Knopf drücken  →  spielen  →  spielen  →  spielen  →  Tabelle

Kein Menü, kein Umstellen, kein Mitschreiben.

## Der Ablauf

```
1.  SPIELRaum sichert den Ist-Zustand der Einstellungsdatei
2.  setzt Variante »Optik«
3.  »Starte das Spiel und spiel ungefähr zehn Minuten«
4.  Beim Spielende: Lauf auswerten, Variante »Ausgeglichen« setzen
5.  »Noch zwei Läufe«
6.  … dasselbe für »Leistung«
7.  Tabelle anzeigen, Variante zur Übernahme anbieten
8.  Ausgangszustand wiederherstellen, falls nichts übernommen wird
```

## Drei Läufe, nicht eine lange Sitzung

Die zehn Minuten müssen **dreimal getrennt** gespielt werden, mit Spielende
dazwischen. Eine halbe Stunde am Stück geht nicht.

Der Grund ist das Spiel, nicht SPIELRaum: Eine Einstellungsdatei wird **beim
Start** gelesen. Ändert man sie, während das Spiel läuft, passiert nichts –
die neuen Werte greifen erst beim nächsten Mal. SPIELRaum kann also nur in
der Lücke zwischen zwei Starts umstellen.

Der Aufwand dafür ist gering: zweimal eine zusätzliche Ladezeit. Bei Road to
Vostok auf der SSD sind das 6,6 Sekunden je Start; auf der alten Festplatte
wären es knapp zwei Minuten gewesen – ein Nebeneffekt, der für den Umzug
spricht.

Die Alternative wäre, den Anwender zwischendurch ins Spielmenü zu schicken.
Genau das soll die Messfahrt aber abnehmen.

## Die eigentliche Schwierigkeit

SPIELRaum läuft **nicht durchgehend**. Es hängt als Umhüllung am Spielstart,
lebt für die Dauer des Spiels und beendet sich mit ihm. Zwischen zwei Läufen
einer Messfahrt existiert kein Prozess, der sich etwas merken könnte.

Die Messfahrt braucht deshalb eine **Fahrtenakte auf der Platte**:

```
~/.local/share/spielraum/fahrten/1963610.json

    spiel            welches Spiel
    angelegt         wann begonnen
    ausgangszustand  die Werte vor dem ersten Eingriff
    varianten        [optik, ausgeglichen, leistung]
    erledigt         welche Läufe schon zählen, mit Messdatei
    naechste         was beim nächsten Spielstart gesetzt wird
```

Das ist dasselbe Muster wie beim [Zustandsjournal](../spielraum/zustand.py),
mit einem Unterschied: Das Journal gilt für **einen** Spielstart und wird am
Ende gelöscht. Die Fahrtenakte überlebt mehrere Starts und wird erst gelöscht,
wenn die Fahrt abgeschlossen oder abgebrochen ist.

Daraus folgt eine Regel: **Der Ausgangszustand steht in der Fahrtenakte, nicht
nur im Journal.** Bricht jemand die Fahrt nach dem zweiten Lauf ab, muss
SPIELRaum wissen, worauf zurückzustellen ist – das Journal des zweiten Laufs
kennt nur den Zustand von Lauf eins.

## Wann ein Lauf zählt

Nicht jeder Spielstart ist eine Messung. Ein Lauf zählt nur, wenn:

* nach Abzug der Ladezeit **mindestens zehn Minuten** übrig sind
  (warum nicht fünf, steht im nächsten Abschnitt),
* das Spiel nicht abgestürzt ist,
* und die Einstellungen während des Laufs unverändert blieben.

Der letzte Punkt braucht eine Prüfung: Wer mitten im Lauf doch ins Spielmenü
geht und etwas verstellt, macht die Messung ungültig. SPIELRaum kann das
erkennen, indem es die Einstellungsdatei nach dem Lauf erneut liest und mit
dem vergleicht, was es gesetzt hatte.

Zählt ein Lauf nicht, wird er verworfen und derselbe Schritt wiederholt – mit
einer Meldung, warum.

## Zehn Minuten, nicht fünf

Die Mindestdauer ist keine Schikane, sondern folgt aus einer Messung vom
01.10.2026. Zwei Läufe desselben Spiels, ohne Änderung dazwischen:

```
 5 Minuten   60,6 Bilder/s
40 Minuten   46,1 Bilder/s
```

Der kurze Lauf zeigte **31 % mehr** – nicht weil etwas besser war, sondern
weil in fünf Minuten zufällig wenig los war. Innerhalb eines einzigen Laufs
schwankte die Bildrate von 30,9 auf 53,8, je nach Ort im Spiel.

Wer drei Varianten mit je fünf Minuten vergleicht, misst die Spielorte und
nennt das Ergebnis dann »optimal«. Zehn Minuten sind das Minimum, bei dem die
Zufälligkeiten sich halbwegs ausmitteln – und auch dann bleibt die Angabe
grob. Siehe [Was diese Messung nicht kann](messen.md).

## Was die Oberfläche sagen muss

Der Knopf heißt **»Messfahrt starten«**, nicht »Optimieren«. Darunter steht,
worauf man sich einlässt:

> Drei Läufe zu je zehn Minuten. Du spielst normal, SPIELRaum stellt
> zwischendurch um. Dauer insgesamt etwa eine halbe Stunde.

Ein Knopf, der »in fünf Minuten die optimalen Werte« verspricht, wäre
gelogen – und zwar nachweisbar.

## Abbruch und Unfälle

| Fall | Was geschieht |
|---|---|
| Nutzer bricht ab | Ausgangszustand aus der Fahrtenakte zurück, Akte löschen |
| Spiel stürzt ab | Lauf zählt nicht, Schritt wird wiederholt |
| Rechner geht aus | Fahrtenakte liegt noch da, beim nächsten Start Nachfrage |
| Spiel wird deinstalliert | Akte verwaist – beim Aufräumen melden und löschen |
| Einstellungen von Hand geändert | Lauf verwerfen, Grund nennen |

Der dritte Fall braucht eine Nachfrage statt stiller Fortsetzung: Wer nach
drei Wochen wieder spielt, erinnert sich nicht an eine halb gelaufene
Messfahrt und wundert sich sonst über fremde Grafikeinstellungen.

## Was danach kommt

**Spiele mit eingebautem Messlauf.** Manche Spiele bringen eine feste Szene
mit, die immer gleich abläuft. Dort entfällt die Streuung durch den Spielort,
und die Messfahrt könnte wirklich vollautomatisch in Minuten laufen – ohne
dass jemand spielt. Ob und wie sich solche Messläufe von außen anstoßen
lassen, ist noch nicht untersucht.

**Mehr als drei Varianten.** Steht die Mechanik, ist die Zahl der Stufen
beliebig. Jede weitere kostet aber zehn Minuten Spielzeit – drei sind das
Vernünftige.
