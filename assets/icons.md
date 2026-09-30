# Icons

Wie aus der gelieferten Datei die Größen im Verzeichnis wurden – damit es
beim nächsten Mal nachvollziehbar ist und nicht wieder geraten werden muss.

## Die Kette

| Datei | Was daran anders ist |
|---|---|
| `icon-quelle.png` | wie geliefert: 1254 × 1254, weißer Rand, Blau `#0061EA` |
| `icon-quelle-sauber.png` | Farben auf die Palette gezogen |
| `icon-transparent.png` | zusätzlich der äußere weiße Rand entfernt |
| `icon-klein.png` | Fassung ohne Schriftzug, Zeichnung größer |
| `icon.png`, `icon-1024.png` … | die fertigen Größen |

## Drei Dinge waren zu tun

**Das Blau stimmte nicht.** Geliefert wurde `#0061EA`, die gemeinsame Palette
in [`farben.md`](farben.md) führt `#1668e3`. Dazu kam Rauschen, wie es bei
erzeugten Bildern üblich ist: Über tausend leicht verschiedene Blautöne um den
Zielwert herum. Beides zusammen mit einem Toleranzbereich eingefangen, danach
stehen 1.119.372 Pixel auf exakt `#1668E3` und 442.187 auf reinem Weiß.

**Der Rand war weiß, nicht durchsichtig.** Bei einem Programmsymbol fällt das
spätestens in einer dunklen Leiste auf – dort klebt dann ein weißes Quadrat um
das Icon. Entfernt wurde er mit einer Füllung von den vier Ecken aus, die nur
den zusammenhängenden Außenbereich erfasst und die weiße Zeichnung in der
Mitte deshalb unberührt lässt: von 442.187 weißen Pixeln blieben 408.379
übrig, die restlichen 34.112 waren der Rahmen.

**Unter 64 Pixeln ist der Schriftzug unlesbar.** Bei 32 Pixeln ist »SPIELRaum«
nur noch ein grauer Streifen, bei 16 Pixeln das ganze Icon ein blauer Fleck.
Deshalb gibt es zwei Fassungen, und die Größen greifen auf verschiedene zu:

    16, 24, 32, 48    ohne Schriftzug (icon-klein.png)
    64 und größer     mit Schriftzug  (icon-transparent.png)

Bei der schriftlosen Fassung reichte es nicht, das Weiß zu übermalen: Zwischen
Schrift und Hintergrund liegen Mischtöne aus der Kantenglättung, und die
blieben beim ersten Versuch als Schatten stehen. Der Toleranzbereich musste
groß genug sein, um das ganze Band zwischen Weiß und Blau zu erfassen.

## Was noch fehlt

Ein `icon.svg`. Alle Fassungen hier stammen aus einem Pixelbild; für eine
Oberfläche, die beliebig skaliert, wäre eine gezeichnete Form besser. Steht
in [`../TODO.md`](../TODO.md).
