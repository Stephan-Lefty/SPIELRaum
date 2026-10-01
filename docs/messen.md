[Deutsch](messen.md) | [Anleitungen](README.md) | [Übersicht](../README.md)

# Was SPIELRaum misst und wie man es liest

## Kurz

```
spielraum messungen                  # alles
spielraum messungen vostok           # auf ein Spiel eingeschränkt
```

Gemessen wird automatisch, sobald ein Spiel über `spielraum starten` läuft
und im Profil `mangohud = true` steht. Die Protokolle landen unter
`~/.local/share/spielraum/messungen/<App-ID>/`.

## Die drei Zahlen

```
102,3 Bilder/s im Mittel, 1-%-Tief 28,6, 0,1-%-Tief 10,4
```

**Das Mittel** ist die bekannteste und die am wenigsten nützliche Zahl. Sie
sagt nichts darüber, wie gleichmäßig das Bild lief.

**Der 1-%-Tiefstwert** ist der Wert, den ein Hundertstel der Stichproben
unterschreitet. Das ist die Zahl, auf die es ankommt: Ruckler spürt man, einen
guten Durchschnitt nicht. Ein Spiel mit 100 Bildern im Mittel und einem
1-%-Tief von 30 fühlt sich schlechter an als eines mit 70 und 60.

**Der 0,1-%-Tiefstwert** ist dasselbe eine Größenordnung weiter unten – die
einzelnen harten Aussetzer.

## Die ersten zehn Sekunden zählen nicht

SPIELRaum verwirft die Aufwärmphase, und das ist kein Detail. Nachgemessen am
30.09.2026 an einem zwanzigsekündigen Lauf:

| | SPIELRaum (ab 10 s) | über den ganzen Lauf |
|---|---|---|
| Mittel | **102,3** | **50,8** |
| 1-%-Tief | 28,6 | 29,3 |
| 0,1-%-Tief | 10,4 | 10,4 |

Der Mittelwert ist **doppelt so hoch**, sobald der Anfang draußen ist. Dort
übersetzt das Spiel Shader und lädt nach; wer das mitrechnet, misst die
Ladezeit. Die Tiefstwerte bleiben dagegen fast gleich – die Ruckler verteilen
sich über den ganzen Lauf.

Zum Vergleich in der Tabelle diente MangoHuds eigene Zusammenfassung
(`*_summary.csv`), die SPIELRaum nicht verwendet: Sie rundet auf eine
Nachkommastelle und rechnet immer über den ganzen Lauf.

## Was ein Unterschied wert ist

Unterschiede unter drei Prozent weist SPIELRaum ausdrücklich als »kein
nennenswerter Unterschied« aus. Zwei Läufe desselben Spiels schwanken auch
ohne Zutun – andere Stelle im Spiel, anderer Hintergrundprozess, wärmere
Grafikkarte. Ein Programm, das jede Schwankung als Erfolg verkauft, ist ein
schlechter Ratgeber.

Für einen belastbaren Vergleich:

* **Dieselbe Stelle im Spiel.** Der Anfang eines Levels lässt sich
  wiederholen, eine Schießerei nicht.
* **Mindestens eine Minute**, besser mehrere.
* **Eine Änderung auf einmal.** Wer Renderer und Shader-Zwischenspeicher
  gleichzeitig umstellt, weiß hinterher nicht, was gewirkt hat.

## Was diese Messung *nicht* kann

Nachgewiesen am 01.10.2026, und der Nachweis geht gegen das eigene
Werkzeug: **Für den Vergleich von Bildraten zwischen zwei Läufen taugt diese
Methode nicht** – jedenfalls nicht bei einem Spiel ohne wiederholbare Szene.

Hier die Bildrate innerhalb *eines einzigen* Laufs von Road to Vostok,
aufgeschlüsselt nach Zweiminutenabschnitten:

```
 0- 2 min:  35,2
 2- 4 min:  30,9
 4- 6 min:  46,3
 6- 8 min:  47,8
 8-10 min:  45,9
10-12 min:  53,8
```

**Von 30,9 auf 53,8 – 74 Prozent Unterschied.** Gleiches Spiel, gleiche
Einstellungen, gleicher Rechner, gleicher Lauf. Der Unterschied ist allein,
wo der Spieler gerade stand und was gerendert werden musste.

Zum Vergleich die Unterschiede, die wir zwischen *verschiedenen* Läufen
gemessen haben und denen wir eine Bedeutung geben wollten:

| Vergleich | Unterschied |
|---|---|
| D3D12 gegen Vulkan | 0,6 % |
| Festplatte gegen SSD | 16 % |
| **innerhalb eines Laufs** | **74 %** |

Die Störgröße ist größer als alles, was wir messen wollten. Ein Mittelwert
aus einem Lauf sagt deshalb vor allem, wo gespielt wurde – nicht, wie gut die
Einstellungen sind.

### Was trotzdem trägt

**Die Ladezeit.** Sie hängt fast ausschließlich am Datenträger und kaum am
Spielgeschehen. Deshalb ist der Umzug von der Festplatte auf die SSD auch
sauber nachgewiesen: 23,8 Sekunden gegen 6,6.

**Die Aussetzer**, mit Einschränkung. Sie entstehen beim Nachladen und hängen
damit ebenfalls am Datenträger – aber eben auch daran, *was* nachgeladen
werden musste.

### Was man bräuchte

Eine wiederholbare Szene: dieselbe Stelle, derselbe Weg, dieselbe Dauer. Die
meisten Spiele geben das nicht her, und Road to Vostok schon gar nicht. Ohne
sie bleibt nur, viele Läufe zu sammeln und auf die Verteilung zu sehen statt
auf einzelne Mittelwerte – was Geduld braucht und trotzdem nie so scharf wird
wie ein Vergleich an derselben Stelle.

Solange das nicht da ist, gilt: **SPIELRaum misst Ladezeiten zuverlässig und
Bildraten nur grob.** Wer das anders darstellt, verkauft Rauschen als
Ergebnis.

## Der Taktregler im Protokoll

MangoHud schreibt in die Kopfzeile jedes Protokolls, welcher Taktregler
während des Laufs galt. SPIELRaum zeigt ihn mit an:

```
  vostok_2026-09-30_20-14-02, Taktregler performance
```

Damit lässt sich nachprüfen, ob GameMode überhaupt gegriffen hat, statt es zu
glauben. Stehen zwei verglichene Läufe auf verschiedenen Reglern, weist
SPIELRaum darauf hin – dann misst man womöglich den Regler und nicht die
Änderung, die man untersuchen wollte.

## Wenn »zu kurz für eine Aussage« dasteht

Nach der Aufwärmzeit müssen mindestens fünfzig Stichproben übrig bleiben. Bei
der üblichen Schrittweite von 100 Millisekunden sind das fünf Sekunden. Kommt
weniger zusammen, gibt SPIELRaum keine Zahl aus – lieber keine als eine, die
auf zwanzig Stichproben beruht.
