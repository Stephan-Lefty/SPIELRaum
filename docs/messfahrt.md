[Deutsch](messfahrt.md) | [Anleitungen](README.md) | [Übersicht](../README.md)

# Die Messfahrt

*Entworfen am 01.10.2026, gebaut am 23.10.2026. Was hier steht, ist
umgesetzt – mit einer Ausnahme, siehe [Was noch fehlt](#was-noch-fehlt).*

## Benutzen

```
spielraum messfahrt <spiel> --starten     # beginnen
spielraum messfahrt <spiel>               # Stand ansehen
spielraum messfahrt <spiel> --abbrechen   # Ausgangszustand zurück
```

Dazwischen: das Spiel ganz normal starten. SPIELRaum setzt vor jedem Lauf
die nächste Variante und trägt das Ergebnis hinterher ein.

Wer nicht alle Varianten messen will – jede kostet zehn Minuten:

```
spielraum messfahrt <spiel> --starten --nur optik,leistung
```

In der Oberfläche führt der Knopf **Messfahrt** durch dasselbe und zeigt am
Ende eine Tabelle mit der Möglichkeit, eine Variante zu übernehmen.

## Von selbst beginnen

```toml
[messen]
fahrt = true
```

Dann beginnt SPIELRaum die Fahrt beim nächsten Spielstart selbst – ohne
dass jemand `--starten` tippt.

**Der Preis:** Die Grafikeinstellungen ändern sich, ohne dass man es
angefordert hat. Wer sich abends hinsetzt und spielen will, findet
womöglich »Optik« vor. Die Vorgabe ist deshalb **aus**; wer es will,
schaltet es pro Spiel ein.

Nach der letzten Variante bleibt die Akte liegen, bis jemand ein Ergebnis
übernimmt oder verwirft. Von selbst beginnt dann keine neue – sonst käme
man nie zum Spielen.

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

## Wer führt: die Oberfläche

Das ist eine Architekturentscheidung, und sie wird besser vorher getroffen
als nachher.

Die Umhüllung (``spielraum starten``) **führt nicht**. Sie setzt, was in der
Fahrtenakte steht, misst und schreibt das Ergebnis zurück – mehr nicht. Sie
startet insbesondere **kein Spiel neu**. Wer nach dem ersten Lauf merkt, dass
er keine Lust mehr hat, soll nicht gegen ein Spiel ankämpfen, das sich von
selbst wieder öffnet.

Geführt wird in der Oberfläche. Sie läuft parallel, sieht in der Fahrtenakte
nach und zeigt nach jedem Lauf den Stand::

    Messfahrt Road to Vostok          Lauf 1 von 3 erledigt

      Optik           61,1 Bilder    1-%-Tief 29,0    ✓
      Ausgeglichen    —                               ← als Nächstes
      Leistung        —

      [ Nächsten Lauf starten ]    [ Abbrechen ]

Der Knopf setzt die nächste Variante und ruft Steam. Wann das geschieht,
entscheidet der Anwender – gleich, nach dem Kaffee oder morgen. Die
Fahrtenakte liegt auf der Platte und wartet.

Das hat einen erwünschten Nebeneffekt: Das Zwischenergebnis steht nach jedem
Lauf da. Wer schon nach »Optik« sieht, dass ihm 61 Bilder reichen, spart sich
die restlichen zwanzig Minuten.

## Der Timer gehört ins Spiel

Woher weiß man, wann die zehn Minuten um sind? Nicht aus einem Fenster im
Hintergrund – im Vollbild sieht man das nicht, und Alt-Tab mitten in der
Messung verfälscht sie.

MangoHud blendet beides mit ein::

    SPIELRaum: Messfahrt 1/3 – Optik
    Noch 7:42

Dafür reichen zwei Einträge in ``MANGOHUD_CONFIG``:

``custom_text_center``
    die Zeile mit Lauf und Variante, fest für die Dauer des Laufs

``exec``
    ruft ein Programm auf, dessen Ausgabe eingeblendet wird – hier die
    Restzeit. SPIELRaum bringt dafür einen eigenen Unterbefehl mit, statt
    ein Shell-Skript daneben zu legen.

Am 01.10.2026 ausprobiert: MangoHud nimmt diese Konfiguration an und schreibt
sein Messprotokoll unverändert weiter. Wie die Einblendung im Spiel aussieht,
muss am echten Spiel beurteilt werden.

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

## Was noch fehlt

**Die Prüfung, ob die Einstellungen während des Laufs unverändert blieben.**
Im Entwurf steht sie als dritte Bedingung dafür, dass ein Lauf zählt. Gebaut
ist sie nicht: Wer mitten im Lauf ins Spielmenü geht und etwas verstellt,
bekommt seinen Lauf trotzdem gezählt.

Der Grund für den Aufschub: Die Prüfung müsste die Einstellungsdatei nach
dem Lauf erneut lesen und mit dem vergleichen, was gesetzt wurde – aber
manche Spiele schreiben beim Beenden ohnehin Werte zurück, die SPIELRaum
nicht gesetzt hat. Ohne zu wissen, welche Felder ein Spiel von sich aus
anfasst, würde die Prüfung gültige Läufe verwerfen. Das wäre schlimmer als
die Lücke.

## Was danach kommt

**Spiele mit eingebautem Messlauf.** Manche Spiele bringen eine feste Szene
mit, die immer gleich abläuft. Dort entfällt die Streuung durch den Spielort,
und die Messfahrt könnte wirklich vollautomatisch in Minuten laufen – ohne
dass jemand spielt. Ob und wie sich solche Messläufe von außen anstoßen
lassen, ist noch nicht untersucht.

**Mehr als drei Varianten.** Steht die Mechanik, ist die Zahl der Stufen
beliebig. Jede weitere kostet aber zehn Minuten Spielzeit – drei sind das
Vernünftige.
