# Den Mod Loader aktuell halten

## Das Problem

Road to Vostok läuft mit dem [Vostok Mod
Loader](https://github.com/ametrocavich/vostok-mod-loader). Der hält **die
Mods** von selbst aktuell: Im Spiel gibt es einen Reiter »Updates«, einen
Knopf »Check for Updates«, und er lädt und tauscht die `.vmz`-Dateien selbst
aus.

**Sich selbst hält er nicht aktuell.** Er prüft nur und zeigt einen Hinweis;
der Knopf heißt »Open Page« und öffnet eine Webseite im Browser. Von dort
muss man herunterladen und den Installer laufen lassen.

Das ist nicht theoretisch. Am 04.11.2026 lief auf dem Rechner die Fassung
3.2.1, während seit dem 06.10.2026 v3.4.2 veröffentlicht war – ein Monat
Rückstand, nur weil der Weg über einen Browser führt.

## Was SPIELRaum macht – und was nicht

| | prüfen | herunterladen | einbauen |
|---|---|---|---|
| Mods | Mod Loader | Mod Loader | Mod Loader |
| Mod Loader selbst | Mod Loader + SPIELRaum | **SPIELRaum** | **SPIELRaum**, auf Verlangen |

Am Mod-Wesen selbst rührt SPIELRaum nicht. Das Herunterladen und Austauschen
der Mods ist der Teil, bei dem etwas kaputtgeht – der Loader benennt beim
Austauschen die Datei um, achtet über `priority` auf die Ladereihenfolge und
verwirft seinen Hook-Zwischenspeicher, wenn sich eine Fassung ändert. Das
nachzubauen hieße, sechzehn Mods aufs Spiel zu setzen, um einen Knopfdruck
zu sparen. Siehe »Was nicht nachgebaut wird« in `CLAUDE.md`.

## Einschalten

Im Profil des Spiels:

```toml
[modloader]

quelle = "vostok"
```

Ohne diesen Abschnitt ist alles aus. Das ist die Vorgabe, und sie hat einen
Grund: SPIELRaum greift sonst **nirgends** ins Netz. Wer das nicht erwartet,
soll es nicht ungefragt bekommen.

Dort steht eine **Kennung**, keine Adresse. Wohin sie zeigt, entscheidet
`modloader.QUELLEN` im Programm. Eine Profildatei kann jeder bearbeiten;
stünde dort eine URL, aus der SPIELRaum eine Datei ins Spielverzeichnis
lädt, wäre das ein Weg hinein – dieselbe Überlegung wie bei `[tasten]`.
Eine neue Quelle wird deshalb im Code eingetragen, nicht im Profil.

## Benutzen

```
spielraum modloader 1963610
```

Zeigt die installierte und die neueste Fassung – und lädt gleich herunter,
falls es etwas Neueres gibt. Das Herunterladen ändert am Spiel **nichts**:
Die Datei landet in `~/.local/share/spielraum/modloader/`. Solange nichts
bestätigt ist, hat sie im Spielordner nichts zu suchen.

```
spielraum modloader 1963610 --einbauen
```

Übernimmt die bereitliegende Fassung. Die alte wird vorher in den
Sicherungsordner des Spiels gelegt.

```
spielraum modloader 1963610 --zurueck
```

Holt die zuletzt gesicherte Fassung zurück.

Mit `--nur-pruefen` wird nur verglichen, nichts geladen.

## Warum Einbauen ein eigener Schritt ist

Herunterladen ist harmlos, Einbauen nicht. Bei einem Fassungswechsel
verwirft der Mod Loader seinen Hook-Zwischenspeicher, löscht seinen Zustand
und setzt die `override.cfg` zurück – im Quelltext ist das
`_static_reset_override_cfg`. Eine neue Fassung kann damit das Zusammenspiel
mit den installierten Mods verändern.

Das soll niemanden in der Sekunde überraschen, in der er spielen wollte.
Deshalb: Prüfen und Holen von selbst, Einbauen auf Verlangen, und ein Weg
zurück, der schon steht, bevor man es wagt.

Der erste Start nach einem Wechsel dauert länger, weil der Zwischenspeicher
neu gebaut wird. Das ist normal und kein Fehler.

## Wann geprüft wird

Beim Spielstart, in einem eigenen Faden, **unmittelbar bevor das Spiel
anläuft**. Eine Netzabfrage *vor* dem Start würde den Start um ihre Laufzeit
verzögern, und das ist das eine, was sie nicht darf. So läuft sie, während
das Spiel ohnehin lädt, und das Ergebnis liegt beim nächsten Nachsehen
bereit.

Der Faden ist ein Tagfaden: Endet das Spiel, während die Abfrage noch hängt,
geht SPIELRaum trotzdem zu Ende. Fehler aus dem Netz werden dort geschluckt
– sie haben mit dem Spiel nichts zu tun, und eine Netzmeldung mitten im
Startprotokoll würde nur verunsichern. Was dabei herauskam, erfährt man beim
nächsten `spielraum modloader`.

Ohne Netz steht dort »nicht geprüft«, und gestartet wird wie immer.

## Was geprüft wird, bevor etwas eingebaut wird

Dass *etwas* ankam, genügt nicht. Die heruntergeladene Datei muss

1. größer als 50 KB sein – das fängt eine Fehlerseite und eine abgebrochene
   Übertragung ab,
2. eine Fassungszeile enthalten,
3. und zwar **dieselbe**, die GitHub als Veröffentlichung nennt.

Punkt 3 fängt den Fall ab, dass eine Veröffentlichung einen Anhang trägt,
der nicht zu ihrer Marke passt. Stimmt eines davon nicht, wird nichts
eingebaut und gesagt, was nicht stimmte.

Die installierte Fassung wird immer aus der **Datei selbst** gelesen
(`MODLOADER_VERSION`), nie aus einem Dateinamen oder einer Notiz daneben.
Ein Dateiname sagt nichts darüber, was wirklich installiert ist.

## Kein Journaleintrag

Das Journal in `zustand.py` beschreibt, was für *einen Spielstart* verstellt
wurde, und wird beim Beenden zurückgenommen. Ein eingebauter Mod Loader soll
bleiben. Stünde er im Journal, würde ihn das Aufräumen nach einem Absturz
wieder entfernen – ein Update, das sich selbst zurücknimmt. Die Rücknahme
läuft deshalb über die Sicherung daneben.

## Ein Vorbehalt

Dass der Loader bei einem Fassungswechsel die `override.cfg` zurücksetzt,
ist nur so lange harmlos, wie das Profil diese Datei nicht selbst anfasst.
Beim Vostok-Profil ist das der Fall – es fasst nur die `Preferences.tres`
an. Käme dort eine `override.cfg`-Stellschraube hinzu, hätten wir denselben
Konflikt wie bei der Tastenbelegung am 03.11.2026: zwei Programme, eine
Datei, und keines weiß vom anderen. Steht als Warnung in `TODO.md`.
