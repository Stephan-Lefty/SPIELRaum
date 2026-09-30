[Deutsch](systemdienst.md) | [Anleitungen](README.md) | [Übersicht](../README.md)

# Was ein Dienst mit Systemrechten kosten würde

Aufgeschrieben am 30.09.2026, weil die Frage aufkam: SPIELRaum fasst die
Grafikkarte nicht an. Das Power-Limit der GTX 1070 steht auf 151 von 170
möglichen Watt, und `nvidia-smi -pl` könnte die 19 Watt freigeben – aber nur
als root. Dafür bräuchte SPIELRaum einen Dienst mit Systemrechten.

Dieses Papier beantwortet zwei Fragen in dieser Reihenfolge: Was brächte es?
Und erst dann: Was kostete es?

## Zuerst: Es bringt nichts

Die Grafikkarte führt selbst Buch darüber, wie lange sie das Power-Limit
ausgebremst hat. Nachgesehen am 30.09.2026, an einem Tag, an dem Road to
Vostok lief:

```
Laufzeit des Rechners:        33.650 s   (9 Stunden 20)
SW Power Capping:                  4,8 s
Anteil:                            0,014 %
```

**Die Karte stößt praktisch nie an ihr Limit.** In über neun Stunden waren es
knapp fünf Sekunden. Die 19 Watt freizugeben würde an diesen fünf Sekunden
etwas ändern und an den übrigen 33.645 nichts.

Der Grund ist, dass diese Karte bei diesen Spielen nicht im Leistungsbereich
arbeitet, wo das Power-Limit greift – sie wartet auf anderes. Bei Road to
Vostok liegt das nahe: Das Spiel liegt auf einer drehenden Platte.

Wer nachrechnen will:

```
nvidia-smi -q -d PERFORMANCE | grep -A4 Counters
cut -d' ' -f1 /proc/uptime
```

Die erste Zahl ist in Mikrosekunden, die zweite in Sekunden.

## Trotzdem: Was es kosten würde

Falls sich das auf anderer Hardware anders darstellt – eine Karte, die
dauernd im Limit hängt, ist ein anderer Fall –, hier die Rechnung.

### 1. Die Angriffsfläche

Das ist der teuerste Posten, und er steht nicht in Stunden.

Ein Dienst als root, der Anfragen von Nutzerprozessen entgegennimmt, ist ein
Rechteübergang. Jeder Fehler darin ist kein Absturz, sondern eine Lücke: Wer
den Dienst dazu bringt, etwas Unvorhergesehenes zu tun, tut es als root. Das
ist kein theoretisches Risiko – es ist die häufigste Art, wie Linux-Systeme
über Anwendungsprogramme übernommen werden.

Konkret wären abzusichern:

* **Die Schnittstelle nimmt keine Pfade und keine Befehle entgegen.** Nur
  Zahlen aus geprüften Bereichen, nur für Geräte, die der Dienst selbst
  aufzählt. Ein Feld, in das ein Pfad passt, ist ein Weg zu beliebigen
  Schreibzugriffen.
* **Wer darf das überhaupt?** Eine Polkit-Regel, die den aktiven Sitzungen
  auf der lokalen Konsole das Recht gibt und sonst niemandem. Ein Dienst
  ohne diese Prüfung lässt jeden Prozess jedes Nutzers mitreden.
* **Die systemd-Unit muss gehärtet sein** – `NoNewPrivileges`,
  `ProtectSystem=strict`, `CapabilityBoundingSet` auf das Nötige beschnitten,
  `SystemCallFilter`. Ein Dienst, der volle root-Rechte behält, obwohl er nur
  in eine Datei unter `/sys` schreiben will, verschenkt jede Eindämmung.

### 2. Der Code

Ungefähr 400 bis 600 Zeilen, verteilt auf:

| Teil | Was |
|---|---|
| Dienst | D-Bus-Schnittstelle, Prüfung, Anwenden, Zurücksetzen |
| Aufräumer | merkt, wenn der Client stirbt, und setzt selbst zurück |
| Client | Gegenstück in SPIELRaum |
| Polkit-Regel | wer darf |
| systemd-Unit | gehärtet |

Der **Aufräumer** ist der unangenehme Teil. Der Dienst überlebt den Client;
wenn SPIELRaum abgeschossen wird, muss er das bemerken und das Power-Limit
selbst zurückstellen. Das Journal auf der Platte hilft hier nicht – es
gehört dem Nutzer, der Dienst darf ihm nicht blind glauben.

### 3. Zwei Distributionen, zweimal Paketierung

Debian 13 führt polkit 126, Manjaro derzeit 127; systemd 257 gegen 261. Die
Schnittstellen sind kompatibel, die **Pfade und Paketkonventionen** aber
nicht: Wohin die Unit gehört, wohin die Polkit-Regel, wie der Dienst beim
Paketbau aktiviert wird und – wichtiger – beim Deinstallieren sauber wieder
verschwindet. Das ist keine schwere, aber eine doppelte Arbeit, und sie
fällt bei jeder Änderung wieder an.

### 4. Testbarkeit

Ein Dienst mit root lässt sich in der CI schlecht prüfen. Die Logik ließe
sich trennen und einzeln testen; dass die Rechteübergabe wirklich hält,
zeigt sich aber nur auf einem echten System. Für den Teil bliebe es beim
Ausprobieren von Hand – auf beiden Distributionen.

### 5. Wartung, dauerhaft

Der Posten, der nie aufhört. Ein Dienst mit Systemrechten ist etwas, wofür
man geradesteht: Meldet jemand eine Lücke, muss sie zeitnah geschlossen und
in beiden Paketen ausgeliefert werden. Bei einem Programm, das Spiele
startet, ist das ein Missverhältnis.

## Empfehlung

**Nicht bauen** – nicht für 19 Watt, die an 0,014 % der Laufzeit etwas
ändern würden.

Die Hebel, die bei dieser Hardware wirklich etwas bewegen, brauchen alle
kein root: der Renderer (D3D12 gegen Vulkan), der Ort des
Shader-Zwischenspeichers, die Einstellungen im Spiel. Was an
Systemstellschrauben nötig ist, macht GameMode – mit einem Dienst, den
andere pflegen und für den andere geradestehen.

## Wann die Rechnung anders ausginge

Drei Fälle, in denen man neu nachdenken sollte:

1. **Die Karte hängt dauernd im Limit.** Wenn `SW Power Capping` einen
   nennenswerten Anteil der Spielzeit ausmacht – ein Zehntel und mehr –,
   ist Leistung zu holen. Das ist bei Karten mit knapp bemessenem
   Power-Limit durchaus üblich.
2. **Es geht nicht um Leistung, sondern um Lautstärke.** Das Power-Limit zu
   *senken* macht manche Karte spürbar leiser, bei wenig Leistungsverlust.
   Dasselbe Werkzeug, anderes Ziel – und ein Ziel, das man ständig will,
   nicht nur beim Spielen.
3. **Jemand anders hat den Dienst schon.** Sollte sich ein gepflegtes
   Projekt finden, das genau diese Schnittstelle anbietet, entfallen Posten
   1, 3 und 5 – und dann ist es eine Anbindung von fünfzig Zeilen statt
   einer eigenen Verantwortung.
