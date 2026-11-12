"""Was SPIELRaum für ein Spiel verstellt – und wie es das zurücknimmt.

Jede Stellschraube hier erfüllt zwei Bedingungen. Erstens: Sie braucht keine
Systemrechte. Was Rechte braucht – Taktregler, GPU-Modus, Prozesspriorität –
macht GameMode, und der hat dafür einen geprüften Dienst. Zweitens: Sie
schreibt ihren alten Zustand ins Journal, **bevor** sie etwas ändert.

Die zweite Bedingung ist der Grund, warum dieses Modul nicht einfach ein paar
``os.environ``-Zuweisungen ist. Ein Programm, das erst ändert und sich dann
merkt, verliert bei einem Absturz dazwischen genau die Information, die es
zum Aufräumen bräuchte.

**Ein Kniff, der viel Zustand spart:** Zwei der wirksamsten Stellschrauben
sind gar keine. Sowohl GameMode als auch die Sperre gegen Bildschirmschoner
und Ruhezustand sind *Wrapper* – Programme, die das Spiel starten und deren
Wirkung endet, wenn der Prozess endet. Da gibt es nichts zurückzusetzen, weil
nie etwas dauerhaft verstellt wurde. Was sich nicht verstellen lässt, kann
auch nicht hängenbleiben.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import time
from pathlib import Path

from . import godot_cfg, godot_tres, tasten, umgebung
from .profil import Profil
from .zustand import Journal


def sicherungsordner(app_id: int | None, name: str) -> Path:
    kennung = str(app_id) if app_id else "".join(
        z if z.isalnum() else "_" for z in name
    )
    return umgebung.daten_verzeichnis() / "sicherungen" / kennung


def messordner() -> Path:
    return umgebung.daten_verzeichnis() / "messungen"


# --- Umgebung ---------------------------------------------------------------


def restzeit_skript(laeuft_bis: float, ueberschrift: str) -> Path:
    """Ein winziges Shell-Skript, dessen Ausgabe MangoHud einblendet.

    **Warum kein Python.** MangoHud ruft ``exec`` mehrmals je Sekunde auf.
    Ein Python-Start kostet jedes Mal rund fünfzig Millisekunden - das wären
    fünf Prozent eines Kerns, nur um eine Uhr anzuzeigen, und zwar während
    einer Messung. Ein ``sh``-Aufruf kostet zwei Millisekunden.

    Das Skript liegt im Laufzeitverzeichnis und verschwindet beim Abmelden.
    """
    pfad = umgebung.laufzeit_verzeichnis() / "restzeit.sh"
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_text(
        "#!/bin/sh\n"
        f"R=$(( {int(laeuft_bis)} - $(date +%s) ))\n"
        'if [ "$R" -le 0 ]; then echo "fertig"; '
        "else printf '%d:%02d\\n' $((R/60)) $((R%60)); fi\n",
        encoding="utf-8",
    )
    pfad.chmod(0o755)
    return pfad


def umgebung_bauen(profil: Profil, messen_in: Path | None = None,
                   laeuft_bis: float | None = None,
                   ueberschrift: str = "") -> dict[str, str]:
    """Die Umgebung für das Spiel zusammenstellen.

    Wichtig: Es wird eine **Kopie** aufgebaut und dem Kindprozess mitgegeben,
    nicht ``os.environ`` des laufenden SPIELRaum verändert. Damit kann diese
    Stellschraube gar nicht hängenbleiben – der Elternprozess bleibt, wie er
    war, und mit ihm jede andere Anwendung.
    """
    werte = dict(os.environ)
    werte.update(profil.variablen)

    if profil.mangohud and umgebung.ermitteln().hat("mangohud"):
        werte["MANGOHUD"] = "1"

        # Wie viel im Bild steht, siehe profil.OVERLAY_UMFAENGE:
        #
        #   voll   alles, was unten aufgezählt ist
        #   klein  nur die Bildrate -- MangoHuds fps_only
        #   aus    no_display
        #
        # WICHTIG BEI »aus«: Dann wird AUCH NICHT GEMESSEN. Belegt am
        # 12.11.2026 mit vkcube, zwei Durchgänge je Einstellung:
        #
        #   voll ............ 55 protokollierte Zeilen
        #   nur Bilder/s .... 55 bis 60 Zeilen
        #   aus ............. 0 Zeilen
        #
        # MangoHuds ``no_display`` hält also nicht nur die Anzeige an,
        # sondern auch das Mitschreiben. Das ist keine Vermutung über
        # MangoHud, sondern zweimal nachgemessen -- nachdem am selben Tag
        # eine ungeprüfte Zusage zu den Tastenkürzeln zurückzunehmen war.
        #
        # »aus« bleibt trotzdem wählbar: Wer die Anzeige wegwill, soll das
        # dürfen. Gesagt wird es dort, wo gewählt wird; in der Oberfläche
        # steht die Folge im Auswahltext selbst.
        # »fahrt«: Beim gewöhnlichen Spielen unsichtbar, bei einer Messfahrt
        # vollständig. Vorgeschlagen am 12.11.2026, und der Ausweg aus dem
        # Widerspruch darüber -- gemessen wird in beiden Fällen.
        #
        # Unsichtbar heißt hier NICHT no_display, sondern durchsichtig:
        # alpha=0 zeichnet weiter und protokolliert dabei (60 Zeilen in der
        # Probe), no_display tut beides nicht. text_outline=0 kommt dazu,
        # weil MangoHud seine Schrift sonst umrandet -- ob die Umrandung
        # die Durchsichtigkeit mitmacht, ließ sich hier nicht nachstellen.
        #
        # Woran eine Messfahrt zu erkennen ist: ``laeuft_bis``. Das setzt
        # starten.py nur, wenn eine Fahrt läuft oder jemand ausdrücklich
        # Minuten verlangt hat.
        umfang = profil.overlay_umfang
        if umfang == "fahrt":
            umfang = "voll" if laeuft_bis is not None else "durchsichtig"

        if umfang == "aus":
            anzeige = ["no_display=1"]
        elif umfang == "durchsichtig":
            anzeige = [
                "fps",
                f"position={profil.overlay_ecke}",
                "alpha=0",
                "background_alpha=0",
                "text_outline=0",
            ]
        elif umfang == "klein":
            # fps_only verträgt sich laut MangoHud.conf.example
            # ausdrücklich nicht mit anderen Anzeigewerten. Deshalb steht
            # hier nur, wo es sitzt und wie deckend der Kasten ist.
            anzeige = [
                "fps_only=1",
                f"position={profil.overlay_ecke}",
                f"background_alpha={profil.overlay_deckkraft}",
                "alpha=1.0",
            ]
        else:
            # Die Auswahl folgt dem, was am 23.10.2026 bei Enshrouded
            # tatsächlich den Unterschied machte:
            #
            #   gpu_temp          Der Hitzeschutz senkte in 11,2 % der Zeit
            #                     den Takt. Ab 83 °C fängt das an.
            #   throttling_status Sagt ausdrücklich, *dass* gedrosselt wird
            #                     -- sonst sieht man nur eine Bildrate, die
            #                     ohne ersichtlichen Grund einbricht.
            #   vram              Lag bei 97,8 % von 8 GB. Ob das stört,
            #                     sieht man erst, wenn es danebensteht.
            #   frame_timing      Ein Einbruch von 45 auf 5 Bilder dauert
            #                     einen Wimpernschlag; im Mittel verschwindet
            #                     er.
            anzeige = [
                "fps", "frametime", "frame_timing=1",
                "gpu_stats", "gpu_temp", "gpu_power", "vram",
                "cpu_stats", "cpu_temp", "ram",
                "throttling_status",
                f"position={profil.overlay_ecke}",
                # Der Kasten hinter der Anzeige. MangoHuds Vorgabe ist 0,5
                # und verdeckt damit ein Stück Bild; siehe
                # profil.overlay_deckkraft. Die Schrift bleibt voll deckend
                # -- durchsichtige Zahlen vor hellem Himmel liest niemand.
                f"background_alpha={profil.overlay_deckkraft}",
                "alpha=1.0",
                # Die Kürzel, mit denen MangoHud die Anzeige umstellen soll.
                # WARNUNG, 12.11.2026: Sie wirkten bei Road to Vostok nicht,
                # und warum, ist ungeklärt. Nicht die Schreibweise (mit
                # vkcube geprüft) und nicht ein fehlender Leseweg (die
                # Bibliothek hängt an libwayland-client und libxkbcommon und
                # lädt libX11.so.6 nach, die hier liegt). Sie bleiben drin,
                # weil sie nichts kosten; versprochen werden sie nicht.
                # Offener Punkt in TODO.md.
                "toggle_hud_position=Shift_R+F11",
                "toggle_hud=Shift_R+F12",
            ]

        if messen_in is not None:
            messen_in.mkdir(parents=True, exist_ok=True)
            # autostart_log zeichnet ab der ersten Sekunde auf; ohne das
            # müsste man im Spiel eine Taste drücken, und dann misst man
            # Sitzungen unterschiedlicher Länge gegeneinander.
            einstellungen = anzeige + [
                f"output_folder={messen_in}",
                "autostart_log=1",
                "log_interval=100",
                "fps_limit=0",
            ]
            # Der Timer gehört ins Bild, nicht in ein Fenster dahinter: Im
            # Vollbild sieht man das nicht, und Alt-Tab mitten in der Messung
            # verfälscht sie.
            if laeuft_bis is not None:
                skript = restzeit_skript(laeuft_bis, ueberschrift)
                if ueberschrift:
                    einstellungen.append(f"custom_text_center={ueberschrift}")
                einstellungen.append("custom_text=Noch")
                einstellungen.append(f"exec={skript}")
            werte["MANGOHUD_CONFIG"] = ",".join(einstellungen)
        else:
            # Kein Messordner heißt: anzeigen, nicht aufzeichnen. Vor dem
            # 23.10.2026 blieb MANGOHUD_CONFIG dann ganz leer, und MangoHud
            # zeigte seine Minimalanzeige -- eine nackte Zahl ohne Einheit.
            werte["MANGOHUD_CONFIG"] = ",".join(anzeige)
    return werte


def befehl_umhuellen(profil: Profil, befehl: list[str]) -> list[str]:
    """GameMode und die Ruhesperre vor den Spielbefehl setzen.

    Reihenfolge von außen nach innen::

        systemd-inhibit  gamemoderun  <Spiel>

    ``systemd-inhibit`` zuerst, weil seine Sperre für alles darunter gelten
    soll. Beide sind Wrapper: Endet das Spiel, endet ihre Wirkung – ohne dass
    jemand etwas zurücksetzen müsste.
    """
    umg = umgebung.ermitteln()
    voll = list(befehl)

    # Die Argumente aus dem Profil gehören ans Ende, hinter den Namen des
    # Programms und alles, was Steam ihm schon mitgibt. Ein Spiel liest
    # seine Befehlszeile von links nach rechts; was vorn steht, gehört noch
    # zu Proton und nicht zum Spiel.
    #
    # Das hat bis 0.3.0 gefehlt: »start.argumente« wurde gelesen, geprüft
    # und in »spielraum pruefen« angezeigt - nur nie angewendet. Wer damit
    # »--rendering-driver vulkan« einschaltete, maß anschließend zweimal
    # dasselbe und hätte daraus geschlossen, Vulkan bringe nichts.
    voll.extend(profil.argumente)

    if profil.gamemode and umg.hat("gamemoderun"):
        voll = [umg.pfad("gamemoderun"), *voll]

    if profil.nicht_stoeren and umg.hat("systemd-inhibit"):
        voll = [
            umg.pfad("systemd-inhibit"),
            "--what=idle:sleep",
            f"--why=SPIELRaum: {profil.name} läuft",
            "--mode=block",
            "--",
            *voll,
        ]
    return voll


# --- Dateien ----------------------------------------------------------------


def _pfad_aufloesen(vorlage: str, spielordner: Path | None, praefix: Path | None) -> Path:
    """``{spielordner}/override.cfg`` in einen echten Pfad übersetzen."""
    if "{spielordner}" in vorlage:
        if spielordner is None:
            raise FileNotFoundError(
                "Das Profil verweist auf {spielordner}, aber das Spiel ist "
                "nicht auffindbar – vermutlich ist es nicht installiert."
            )
        vorlage = vorlage.replace("{spielordner}", str(spielordner))
    if "{praefix}" in vorlage:
        if praefix is None:
            raise FileNotFoundError(
                "Das Profil verweist auf {praefix}, aber es gibt kein "
                "Proton-Präfix – läuft das Spiel nativ?"
            )
        vorlage = vorlage.replace("{praefix}", str(praefix))
    return Path(vorlage)


def atomar_schreiben(ziel: Path, text: str) -> None:
    """Eine Einstellungsdatei des Spiels atomar ersetzen.

    Daneben schreiben, dann umbenennen – dasselbe Verfahren wie beim Journal
    und aus demselben Grund: Eine halb geschriebene Einstellungsdatei sieht
    gültig aus. Bei einer ``.tres`` mit Tastenbelegungen darin heißt »halb
    geschrieben« im schlimmsten Fall ein Spiel, in dem nichts mehr reagiert.

    Die Zwischendatei liegt im Zielverzeichnis, nicht in ``/tmp``:
    ``os.replace`` ist nur innerhalb eines Dateisystems atomar, und das
    Proton-Präfix liegt hier auf einer anderen Platte als ``/tmp``.
    """
    ziel.parent.mkdir(parents=True, exist_ok=True)
    griff, zwischendatei = tempfile.mkstemp(dir=ziel.parent, suffix=".tmp")
    try:
        with os.fdopen(griff, "w", encoding="utf-8") as datei:
            datei.write(text)
            datei.flush()
            os.fsync(datei.fileno())
        os.replace(zwischendatei, ziel)
    except BaseException:
        Path(zwischendatei).unlink(missing_ok=True)
        raise


def alte_werte(aenderung, text: str, werte: dict) -> tuple[dict, list[str]]:
    """Was die Schlüssel enthalten, die wir gleich ändern wollen.

    Als Text, unverändert wie sie dastehen – beide Leser geben das so
    zurück. Das ist Absicht: Schreibt man denselben Text zurück, steht
    hinterher Zeichen für Zeichen dasselbe da. Eine Umwandlung nach Zahl und
    zurück würde aus ``1.0`` ein ``1`` machen und damit den Typ ändern, auf
    den das Spiel sich verlässt.

    **Ein fehlender Schlüssel ist selbst ein Wert.** Steht er noch nicht in
    der Datei, merkt sich das Journal ein ``None`` – zurückgesetzt heißt dann
    nicht »alten Wert schreiben«, sondern »die Zeile wieder entfernen«. Ohne
    diese Unterscheidung bliebe nach dem Zurücksetzen eine Zeile stehen, die
    SPIELRaum selbst erfunden hat.

    Zurück kommen die alten Werte und die Namen der Abschnitte, die es
    vorher überhaupt nicht gab – von denen muss später auch die Kopfzeile
    weichen.
    """
    if aenderung.art == "godot-tres":
        # Bei der ``.tres`` kann kein Schlüssel fehlen: ``schreiben`` legt
        # keine an und weist unbekannte Namen zurück (streng=True). Was hier
        # nicht dasteht, wird also auch nie geschrieben.
        vorhanden = godot_tres.lesen(text)
        return {k: vorhanden[k] for k in werte if k in vorhanden}, []

    vorhanden = godot_cfg.lesen(text)
    gesammelt: dict[str, dict[str, str | None]] = {}
    fehlende_abschnitte: list[str] = []
    for abschnitt, schluessel in werte.items():
        if abschnitt not in vorhanden:
            fehlende_abschnitte.append(abschnitt)
        da = vorhanden.get(abschnitt, {})
        gesammelt[abschnitt] = {k: da.get(k) for k in schluessel}
    return gesammelt, sorted(fehlende_abschnitte)


def _werte_einsetzen(art: str | None, text: str, werte: dict,
                     fehlende_abschnitte: list[str] | None = None) -> str:
    """Die alten Werte zurück in den *aktuellen* Dateiinhalt schreiben.

    Zwei Richtungen in einem Durchgang: Was einen alten Wert hat, wird auf
    ihn zurückgesetzt; was vorher nicht dastand (``None``), wird entfernt.

    ``streng=False`` bei der ``.tres``: Hat das Spiel einen Schlüssel
    inzwischen selbst entfernt, soll das Zurücksetzen nicht abbrechen und
    die übrigen Werte stehen lassen. Was nicht ankommt, meldet der Aufrufer.
    """
    if art == "godot-tres":
        da = {k: v for k, v in werte.items() if v is not None}
        return godot_tres.schreiben(text, da, streng=False)

    setzen = {a: {k: v for k, v in s.items() if v is not None}
              for a, s in werte.items()}
    weg = {a: [k for k, v in s.items() if v is None] for a, s in werte.items()}

    ergebnis = godot_cfg.zusammenfuehren(text, {a: s for a, s in setzen.items() if s})
    if any(weg.values()) or fehlende_abschnitte:
        ergebnis = godot_cfg.entfernen(ergebnis, weg, fehlende_abschnitte)
    return ergebnis


def _flach(werte: dict) -> list[str]:
    """Die Schlüssel einer flachen oder verschachtelten Wertetabelle benennen."""
    namen: list[str] = []
    for schluessel, wert in werte.items():
        if isinstance(wert, dict):
            namen.extend(f"{schluessel}.{k}" for k in wert)
        else:
            namen.append(schluessel)
    return sorted(namen)


def _neuer_inhalt(aenderung, alt: str, werte: dict) -> str:
    """Den neuen Dateiinhalt bauen – je nach Format mit dem passenden Leser.

    Beide Leser arbeiten zeilenweise und lassen alles unangetastet, was nicht
    ausdrücklich geändert wird. Das ist bei fremden Dateien keine Höflichkeit,
    sondern Notwendigkeit: In der Preferences.tres von Road to Vostok stehen
    neben den Grafikeinstellungen die Tastenbelegungen.
    """
    if aenderung.art == "godot-tres":
        if alt:
            godot_tres.pruefen(alt)
        elif not alt:
            raise FileNotFoundError(
                "Für godot-tres muss die Datei schon da sein - eine "
                "Godot-Ressource lässt sich nicht sinnvoll aus dem Nichts "
                "anlegen. Das Spiel schreibt sie beim ersten Start."
            )
        return godot_tres.schreiben(alt, werte)

    if aenderung.zusammenfuehren:
        return godot_cfg.zusammenfuehren(alt, werte)
    return godot_cfg.zusammenfuehren("", werte)


def dateien_anwenden(
    profil: Profil,
    journal: Journal,
    spielordner: Path | None = None,
    praefix: Path | None = None,
    variante: str | None = None,
) -> list[str]:
    """Die Einstellungsdateien des Spiels anpassen – jede mit Sicherung.

    Gibt zurück, was getan wurde, damit der Anwender es liest, statt es zu
    erraten. Die Sicherung wird mit ``shutil.copy2`` angelegt, also samt
    Zeitstempeln: Manche Spiele entscheiden anhand des Änderungsdatums, ob
    sie eine Datei neu einlesen.
    """
    getan: list[str] = []

    # Eine Variante überschreibt, was fest im Profil steht. Sie ersetzt die
    # Werte nicht nur - sie ist der ganze Grund, warum die Datei angefasst
    # wird. Steht keine Variante an, gilt, was unter [dateien] hinterlegt ist.
    gewaehlt = profil.varianten.get(variante) if variante else None
    if variante and gewaehlt is None:
        raise ValueError(
            f"Das Profil kennt keine Variante »{variante}«. Vorhanden: "
            + (", ".join(profil.varianten) or "keine")
        )

    for kennung, aenderung in profil.dateien.items():
        ziel = _pfad_aufloesen(aenderung.pfad, spielordner, praefix)

        werte = gewaehlt.dateien.get(kennung, {}) if gewaehlt else aenderung.werte
        if not werte:
            continue

        if ziel.exists():
            ordner = sicherungsordner(profil.steam_app_id, profil.name)
            ordner.mkdir(parents=True, exist_ok=True)
            sicherung = ordner / f"{ziel.name}.{time.strftime('%Y%m%d-%H%M%S')}"
            shutil.copy2(ziel, sicherung)
            alt = ziel.read_text(encoding="utf-8", errors="replace")
            # Erst ins Journal, dann ändern. Andersherum wäre ein Absturz
            # zwischen beiden Schritten nicht mehr aufzulösen.
            #
            # Im Journal stehen die alten Werte der angefassten Schlüssel,
            # nicht nur der Pfad der Sicherung: Zurückgesetzt wird damit
            # genau unsere Änderung und nicht alles, was das Spiel seither
            # selbst in die Datei geschrieben hat. Siehe zustand.py.
            alt_werte, fehlende = alte_werte(aenderung, alt, werte)
            journal.vermerken("datei", str(ziel), str(sicherung),
                              art=aenderung.art, alt_werte=alt_werte,
                              fehlende_abschnitte=fehlende)
        else:
            alt = ""
            # Kein Vorher heißt: beim Zurücksetzen wieder löschen.
            journal.vermerken("datei", str(ziel), None, art=aenderung.art)

        neu = _neuer_inhalt(aenderung, alt, werte)

        atomar_schreiben(ziel, neu)
        getan.append(f"{kennung}: {ziel}")

    return getan


def zuruecksetzen(journal: Journal) -> list[str]:
    """Alles aus dem Journal rückgängig machen.

    In umgekehrter Reihenfolge, weil spätere Änderungen auf früheren
    aufbauen können. Und mit Fehlertoleranz: Wenn ein Eintrag sich nicht
    zurücksetzen lässt, werden die übrigen trotzdem abgearbeitet. Ein
    Aufräumer, der beim ersten Problem stehenbleibt, hinterlässt mehr
    Unordnung als einer, der weitermacht und berichtet.
    """
    bericht: list[str] = []

    for eintrag in reversed(journal.eintraege):
        # Tasten gehen nicht über eine Sicherungskopie zurück, sondern über
        # einen Befehl an keyd: Es gibt keine Datei, in der der alte Zustand
        # stünde, weil der alte Zustand »gar keine Umbelegung« war.
        if eintrag.stellschraube == tasten.STELLSCHRAUBE:
            bericht.append(tasten.zuruecknehmen())
            continue

        if eintrag.stellschraube != "datei":
            bericht.append(f"unbekannte Stellschraube: {eintrag.stellschraube}")
            continue

        ziel = Path(eintrag.ziel)
        try:
            if eintrag.vorher is None:
                ziel.unlink(missing_ok=True)
                bericht.append(f"{ziel} wieder entfernt")
            elif eintrag.alt_werte:
                bericht.append(_werte_zurueck(eintrag, ziel))
            else:
                # Journal der Fassung 1, oder eine Datei ohne angefasste
                # Schlüssel. Dann bleibt nur der alte Weg – die ganze
                # Sicherung zurück. Er setzt zu viel zurück; das ist beim
                # Aufräumen hinter einer älteren Fassung aber besser als
                # nichts zurückzusetzen.
                sicherung = Path(eintrag.vorher)
                if not sicherung.exists():
                    bericht.append(f"FEHLT: Sicherung {sicherung} für {ziel}")
                    continue
                shutil.copy2(sicherung, ziel)
                bericht.append(f"{ziel} aus Sicherung wiederhergestellt (ganze Datei)")
        except OSError as fehler:
            bericht.append(f"FEHLER bei {ziel}: {fehler}")

    return bericht


def _werte_zurueck(eintrag, ziel: Path) -> str:
    """Nur die angefassten Schlüssel auf ihren alten Wert zurückschreiben.

    Der eigentliche Zweck des Umbaus vom 03.11.2026. Gelesen wird der
    **aktuelle** Dateiinhalt, nicht die Sicherung: Was das Spiel seither
    selbst hineingeschrieben hat, soll ja gerade stehen bleiben.

    Ist die Datei verschwunden, greift die Vollsicherung – dann gibt es
    nichts mehr, in das sich einzelne Werte zurückschreiben ließen.
    """
    if not ziel.exists():
        sicherung = Path(eintrag.vorher) if eintrag.vorher else None
        if sicherung is not None and sicherung.exists():
            shutil.copy2(sicherung, ziel)
            return f"{ziel} war weg – ganz aus Sicherung wiederhergestellt"
        return f"FEHLT: {ziel} ist weg und es gibt keine Sicherung"

    jetzt = ziel.read_text(encoding="utf-8", errors="replace")
    neu = _werte_einsetzen(eintrag.art, jetzt, eintrag.alt_werte,
                           eintrag.fehlende_abschnitte)

    namen = _flach(eintrag.alt_werte)
    if neu == jetzt:
        return f"{ziel}: stand schon wieder auf {', '.join(namen)}"

    atomar_schreiben(ziel, neu)

    # Nachsehen, ob jedes Wort auch angekommen ist. Beim Zurücksetzen wird
    # ohne ``streng`` geschrieben, damit ein inzwischen entfernter Schlüssel
    # den Rest nicht aufhält – dann muss aber auffallen, dass er fehlt.
    offen = _nicht_angekommen(eintrag, neu)
    if offen:
        return (f"{ziel}: zurückgesetzt, aber nicht angekommen: "
                + ", ".join(offen))
    return f"{ziel}: {len(namen)} Werte zurückgesetzt ({', '.join(namen)})"


def _nicht_angekommen(eintrag, text: str) -> list[str]:
    """Welche der alten Zustände stehen hinterher *nicht* in der Datei?

    Ein ``None`` im Journal heißt »gab es vorher nicht«. Angekommen ist das
    dann, wenn der Schlüssel jetzt fehlt – nicht, wenn er einen Wert hat.
    """
    if eintrag.art == "godot-tres":
        jetzt = godot_tres.lesen(text)
        return sorted(k for k, v in eintrag.alt_werte.items()
                      if v is not None and jetzt.get(k) != v)

    jetzt = godot_cfg.lesen(text)
    fehlend: list[str] = []
    for abschnitt, schluessel in eintrag.alt_werte.items():
        da = jetzt.get(abschnitt, {})
        for k, v in schluessel.items():
            if v is None:
                if k in da:
                    fehlend.append(f"{abschnitt}.{k}")
            elif da.get(k) != v:
                fehlend.append(f"{abschnitt}.{k}")
    return sorted(fehlend)
