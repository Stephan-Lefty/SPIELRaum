[Deutsch](gamemode.md) | [Anleitungen](README.md) | [Übersicht](../README.md)

# GameMode darf nicht immer, was es soll

Aufgeschrieben am 30.09.2026, nach dem ersten Messlauf mit einem echten
Spiel. Der Befund war unerwartet und betrifft jeden, der SPIELRaum auf
Arch oder Manjaro benutzt.

## Was passiert ist

Im Messprotokoll stand der Taktregler auf `powersave` – obwohl GameMode
eingeschaltet war und auch lief. Der Dienst startete mit dem Spiel, sah die
Clients und tat trotzdem nichts am Takt.

Der Grund stand im Systemprotokoll:

```
pkexec: Not authorized [USER=root]
  [COMMAND=/usr/lib/gamemode/procsysctl split_lock_mitigate 1]
```

Und die Ursache in der mitgelieferten Polkit-Regel
(`/usr/share/polkit-1/actions/com.feralinteractive.GameMode.policy`):

```xml
<action id="com.feralinteractive.GameMode.governor-helper">
  <description>Modify the CPU governor</description>
  <defaults>
    <allow_any>no</allow_any>
    <allow_inactive>no</allow_inactive>
    <allow_active>no</allow_active>
  </defaults>
</action>
```

**Dreimal `no`.** Auch der angemeldete Nutzer an der lokalen Konsole darf den
Taktregler nicht ändern. Das ist kein Fehler des Pakets, sondern eine bewusst
zurückhaltende Voreinstellung: Wer sie ändert, entscheidet sich dafür, dass
ein Programm ohne Rückfrage an Systemeinstellungen darf.

## Warum SPIELRaum es trotzdem nicht selbst macht

Es wäre naheliegend, die Regel bei der Einrichtung einfach mitzuliefern.
`install.sh` tut das ausdrücklich **nicht**, und das bleibt so.

Eine Polkit-Regel zu setzen heißt, Rechte zu vergeben. Das ist eine
Entscheidung des Menschen vor dem Rechner, nicht eines Einrichtungsskripts,
das jemand ausführt, um Spiele flüssiger zu bekommen. Ein Programm, das im
Vorbeigehen Berechtigungen ausweitet, ist genau das, was man nicht auf dem
Rechner haben will – auch dann nicht, wenn es die eigene Absicht trifft.

## Wenn man es will

Die Regel gehört nach `/etc/polkit-1/rules.d/`. Sie gibt den Helfern von
GameMode das Recht, aber nur für angemeldete Sitzungen an der lokalen
Konsole – nicht für Dienste, nicht über das Netz:

```javascript
// /etc/polkit-1/rules.d/49-gamemode.rules
polkit.addRule(function(action, subject) {
    if (action.id.indexOf("com.feralinteractive.GameMode.") === 0 &&
        subject.local && subject.active) {
        return polkit.Result.YES;
    }
});
```

Danach den Dienst neu starten:

```
systemctl --user restart gamemoded
```

Ob es gewirkt hat, zeigt der nächste Messlauf: In der Zeile zum Protokoll
steht dann `Taktregler performance` statt `powersave`.

## Ob es sich lohnt

Auf dem Rechner, auf dem SPIELRaum entstand: vermutlich wenig. Der
Taktregler heißt dort zwar `powersave`, die Energievorgabe daneben steht aber
auf `performance`:

```
scaling_governor:                powersave
energy_performance_preference:   performance
```

Bei `intel_pstate` entscheidet die zweite Zeile, wie schnell hochgetaktet
wird. Die CPU springt also längst an. Der Tipp »Governor auf performance« ist
für Systeme gedacht, wo beides auf Sparen steht.

Deshalb die Reihenfolge: **erst messen, dann Rechte vergeben.** Nicht
umgekehrt.
