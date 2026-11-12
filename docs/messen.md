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

## Die CPU-Last verrät, ob jemand mitlief

Seit dem 12.11.2026 führt SPIELRaum die mittlere CPU-Last jedes Laufs mit:

```
  RTV_2026-11-12_15-21-19, Taktregler powersave
      46.9 Bilder/s im Mittel, 1-%-Tief 17.4, 0,1-%-Tief 0.1
      Ladezeit 10 s, dazu 7.5 s Aussetzer im Spiel, CPU-Last 59 %
```

Sie steht nicht da, weil sie interessant wäre, sondern weil sie die Frage
beantwortet, ob der Lauf überhaupt etwas über das Spiel aussagt. Liegen zwei
verglichene Läufe mehr als zehn Prozentpunkte auseinander, sagt SPIELRaum es:

```
  CPU-Last       24.9  ->    59.1   +34.3 Punkte
  Achtung: Die CPU-Last unterscheidet sich um 34 Prozentpunkte (25 % gegen
  59 %). Beim zweiten Lauf lief vermutlich etwas mit …
```

**Der Anlass.** An diesem Tag nahm OBS während eines Messlaufs auf und
kodierte dabei auf dem Prozessor. Aufgefallen ist es nur, weil die Aufnahme
mitten im Lauf endete – danach sprang die Bildrate von 48,8 auf 57,7. Gegen
denselben Streckenabschnitt zwei Tage davor gerechnet:

```
Minute  2-10, OBS läuft .....  39,1 gegen 47,2     -17,3 %
Minute 11-12, OBS aus .......  56,0 gegen 53,8      +4,1 %
```

**17 Prozent** – mehr, als in diesem Projekt je eine Einstellung gebracht
hat. Und es stand die ganze Zeit in der Messdatei, Spalte `cpu_load`: 26 bis
29 Prozent in den sauberen Läufen gegen 69 in diesem. Niemand hat
hingesehen, und zwei falsche Schlüsse landeten im Repo, bevor es auffiel.

Gewarnt wird erst ab einer Minute gemessener Spielzeit. Ohne diese Grenze
stützte sich die Warnung auf einen Lauf von **13 Sekunden** – eine Zahl aus
zu wenig Material, also genau der Fehler, den sie verhindern soll. Die
CPU-Last steht für kurze Läufe weiter in der Liste, nur verglichen wird sie
nicht.

Die zehn Prozentpunkte sind eine Hausnummer aus vier Läufen, keine
hergeleitete Schwelle; die Rechnung steht bei `messen.MITLAEUFER_SPANNE`.
Verglichen wird nur die **Differenz zwischen zwei Läufen desselben Spiels** –
ein absoluter Grenzwert wäre falsch, denn 70 Prozent CPU-Last können beim
einen Spiel der Mitläufer und beim nächsten der Normalfall sein.

SPIELRaum **sagt** es und verwirft nichts von selbst. Es kann der Mitläufer
gewesen sein, es kann auch die Stelle im Spiel gewesen sein. Welches von
beidem, weiß das Protokoll nicht – und was es nicht weiß, soll es nicht
entscheiden.

## Die Anzeige im Spiel

Sie sitzt oben links, lässt sich pro Profil woanders hinlegen und ist zu
einem Viertel deckend:

```toml
[messen]
ecke      = "top-right"   # top/middle/bottom je links oder rechts
deckkraft = 0.25          # 0 = kein Kasten, 1 = voll deckend
```

`deckkraft` betrifft nur den Kasten hinter den Zahlen. Die Schrift bleibt
voll deckend – durchsichtige Zahlen vor einem hellen Himmel kann man nicht
lesen. Bei `0` steht die Schrift ohne Kasten im Bild und bleibt lesbar, weil
MangoHud die Buchstaben umrandet.

**Im Spiel, ohne es zu beenden:**

```
Shift rechts + F11     eine Stelle weiter
Shift rechts + F12     Anzeige aus und wieder an
```

Frei mit der Maus ziehen geht nicht; MangoHud 0.8.4 kennt das nicht. Die
Taste schaltet durch die sechs Stellen, die es kennt. Wer eine davon dauerhaft
will, schreibt sie als `ecke` ins Profil – die Taste wirkt nur für die
laufende Sitzung.

## Die Aufnahmen aus dem Spiel

Steam legt sie an einer Stelle ab, die niemand errät:

```
~/.local/share/Steam/userdata/<Konto-Nummer>/760/remote/<App-ID>/screenshots/
```

Die `760` ist Steams eigene App-Nummer für die Aufnahmefunktion, die
Konto-Nummer ist die Steam3-ID. Daneben liegt ein `thumbnails`-Ordner mit den
Vorschaubildern.

In der Oberfläche steht dafür rechts neben »Mod Loader einbauen« der Knopf
**Aufnahmen**, mit der Anzahl darauf. Er bleibt grau, wenn keine vorliegt --
Steam legt den Ordner schon beim ersten Spielstart an, »Ordner vorhanden«
sagt also nichts. Im Spiel macht **F12** eine Aufnahme.

Sucht man den Ordner von Hand, lohnt der Hinweis, dass `~/.steam/steam`
meist nur ein Verweis auf `~/.local/share/Steam` ist. Beide Pfade führen zum
selben Ordner; SPIELRaum löst das auf, damit es nicht doppelt zählt.

## Wenn »zu kurz für eine Aussage« dasteht

Nach der Aufwärmzeit müssen mindestens fünfzig Stichproben übrig bleiben. Bei
der üblichen Schrittweite von 100 Millisekunden sind das fünf Sekunden. Kommt
weniger zusammen, gibt SPIELRaum keine Zahl aus – lieber keine als eine, die
auf zwanzig Stichproben beruht.
