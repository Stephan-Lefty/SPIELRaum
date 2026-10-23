"""Das Hauptfenster: Spiele links, Befund rechts.

Der Entwurf folgt einer Lehre aus dem 01.10.2026. An dem Tag stellte sich
heraus, dass von allem, was SPIELRaum für Road to Vostok eingestellt hatte,
genau **eine** Sache nachweislich wirkte – und drei Umgebungsvariablen gar
nichts taten, weil sie für OpenGL gedacht sind und das Spiel Vulkan fährt.

Eine Oberfläche, die daraufhin »Optimiert!« meldet, wäre eine Lüge mit
Knöpfen. Deshalb zeigt dieses Fenster nicht, was SPIELRaum *tun könnte*,
sondern was **gemessen** ist – und sagt ausdrücklich dazu, wenn nichts
gemessen wurde.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QMainWindow, QMessageBox, QPushButton, QSplitter, QTextBrowser,
    QVBoxLayout, QWidget,
)

from .. import (__version__, farben, messen, profil, stellschrauben, steam,
                tasten, umgebung, zustand)


# Wie keyd die Tasten nennt und wie sie auf einer deutschen Tastatur
# beschriftet sind. Nur die, die sich unterscheiden -- »w« heißt »w«.
TASTENNAMEN = {
    "up": "Pfeil hoch", "down": "Pfeil runter",
    "left": "Pfeil links", "right": "Pfeil rechts",
    "pageup": "Bild hoch", "pagedown": "Bild runter",
    "home": "Pos 1", "end": "Ende", "insert": "Einfg", "delete": "Entf",
    "space": "Leertaste", "enter": "Enter", "esc": "Esc",
    "leftshift": "Umschalt links", "rightshift": "Umschalt rechts",
    "leftcontrol": "Strg links", "rightcontrol": "Strg rechts",
    "leftalt": "Alt links", "rightalt": "Alt Gr",
    "layer(shift)": "Umschalt", "layer(control)": "Strg",
    "layer(alt)": "Alt", "layer(meta)": "Meta",
}


def _tastenblatt(spiel: steam.Spiel) -> Path | None:
    """Das eigene Tastenblatt zu diesem Spiel, falls eines erzeugt wurde.

    Liegt im Ordner ``tastenblaetter/`` und wird von Git ignoriert: Die
    Belegung hängt an der Hand, die die Maus führt, und an den Tastaturen,
    die auf dem Tisch stehen. Sie gehört niemandem sonst.

    Erzeugt wird sie mit ``werkzeuge/tastenblatt.py``.
    """
    ordner = Path(__file__).resolve().parent.parent.parent / "tastenblaetter"
    if not ordner.is_dir():
        return None
    # Nach dem Spielnamen suchen, nicht nach der App-ID: Die Dateien sind
    # zum Lesen gedacht, nicht zum Nachschlagen durch ein Programm.
    stamm = spiel.name.replace(" ", "-")
    for endung in (".pdf", ".md", ".html"):
        treffer = sorted(ordner.glob(f"{stamm}*{endung}"))
        if treffer:
            return treffer[0]
    return None


def _tastenname(name: str) -> str:
    """Den keyd-Namen so zeigen, wie die Taste beschriftet ist.

    ``pageup`` steht auf keiner deutschen Tastatur. Wer in der Übersicht
    nachsieht, sucht »Bild hoch«.
    """
    return TASTENNAMEN.get(name, name.upper() if len(name) == 1 else name)


def _stil() -> str:
    """Das Aussehen, aus der gemeinsamen Palette.

    Keine Zahlen von Hand: Die Werte stammen aus ``spielraum/farben.py``,
    das unverändert aus den anderen Programmen übernommen ist.
    """
    return f"""
    QMainWindow, QWidget {{
        background: {farben.GRAU_PAPIER};
        color: {farben.GRAU};
    }}
    QListWidget {{
        background: white;
        border: 1px solid {farben.GRAU_HELL};
        border-radius: 6px;
        padding: 4px;
        font-size: 11pt;
    }}
    QListWidget::item {{ padding: 7px 6px; border-radius: 4px; }}
    QListWidget::item:selected {{ background: {farben.BLAU}; color: white; }}
    QTextBrowser {{
        background: white;
        border: 1px solid {farben.GRAU_HELL};
        border-radius: 6px;
        padding: 10px;
        font-size: 10.5pt;
    }}
    QPushButton {{
        background: {farben.BLAU};
        color: white;
        border: none;
        border-radius: 6px;
        padding: 9px 18px;
        font-weight: bold;
    }}
    QPushButton:hover {{ background: {farben.BLAU_HELL}; }}
    QPushButton:disabled {{ background: {farben.GRAU_HELL}; color: {farben.GRAU_LEISE}; }}
    QLabel#ueberschrift {{
        color: {farben.GRAU_DUNKEL};
        font-size: 15pt;
        font-weight: bold;
    }}
    QLabel#unterzeile {{ color: {farben.GRAU_LEISE}; font-size: 9.5pt; }}
    """


class Fenster(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"SPIELRaum {__version__}")
        self.resize(1000, 640)
        self.setStyleSheet(_stil())

        symbol = Path(__file__).resolve().parent.parent.parent / "assets" / "icon-128.png"
        if symbol.exists():
            self.setWindowIcon(QIcon(str(symbol)))

        self.spiele: list[steam.Spiel] = []

        kopf = QLabel("SPIELRaum")
        kopf.setObjectName("ueberschrift")
        umg = umgebung.ermitteln()
        unter = QLabel(f"{umg.name} · Spiel wählen, dann steht rechts, was gemessen ist")
        unter.setObjectName("unterzeile")

        self.liste = QListWidget()
        self.liste.currentRowChanged.connect(self._gewaehlt)

        self.befund = QTextBrowser()
        self.befund.setOpenExternalLinks(True)

        self.knopf_start = QPushButton("Über Steam starten")
        self.knopf_start.clicked.connect(self._starten)
        self.knopf_start.setEnabled(False)
        self.knopf_neu = QPushButton("Neu einlesen")
        self.knopf_neu.clicked.connect(self._einlesen)

        # Tasten von Hand umlegen. Im Normalfall braucht es diesen Knopf
        # nicht -- beim Start über SPIELRaum passiert das von allein. Er ist
        # für den Fall, dass jemand ein Spiel direkt über Steam startet und
        # die Belegung trotzdem haben will.
        self.tasten_liegen = False
        self.knopf_tasten = QPushButton("Belegung jetzt setzen")
        self.knopf_tasten.clicked.connect(self._tasten_umschalten)
        self.knopf_tasten.setToolTip(
            "Setzt die Tastenbelegung dieses Spiels sofort, ohne es zu starten.\n"
            "Beim Start über SPIELRaum passiert das von allein.")
        self.knopf_tasten.setEnabled(False)

        knoepfe = QHBoxLayout()
        knoepfe.addWidget(self.knopf_neu)
        knoepfe.addWidget(self.knopf_tasten)
        knoepfe.addStretch()
        knoepfe.addWidget(self.knopf_start)

        links = QVBoxLayout()
        links.addWidget(QLabel("Installierte Spiele"))
        links.addWidget(self.liste)
        linksW = QWidget()
        linksW.setLayout(links)

        rechts = QVBoxLayout()
        rechts.addWidget(QLabel("Befund"))
        rechts.addWidget(self.befund)
        rechtsW = QWidget()
        rechtsW.setLayout(rechts)

        teiler = QSplitter(Qt.Horizontal)
        teiler.addWidget(linksW)
        teiler.addWidget(rechtsW)
        teiler.setSizes([340, 660])

        haupt = QVBoxLayout()
        haupt.addWidget(kopf)
        haupt.addWidget(unter)
        haupt.addSpacing(8)
        haupt.addWidget(teiler, 1)
        haupt.addLayout(knoepfe)

        mitte = QWidget()
        mitte.setLayout(haupt)
        self.setCentralWidget(mitte)

        self._einlesen()

    # --- Daten ------------------------------------------------------------

    def _einlesen(self) -> None:
        self.liste.clear()
        self.spiele = steam.spiele_finden()
        for spiel in self.spiele:
            dreht = umgebung.platte_dreht(spiel.ordner)
            hat = profil.finden(steam_app_id=spiel.app_id) is not None
            zeichen = "●" if hat else "○"
            platte = " ⚠ dreht" if dreht else ""
            eintrag = QListWidgetItem(f"{zeichen}  {spiel.name}{platte}")
            if dreht:
                eintrag.setToolTip(
                    "Liegt auf einer drehenden Platte. Das kostet Ladezeit "
                    "und verursacht Nachladehänger – mehr als jede Einstellung."
                )
            self.liste.addItem(eintrag)

        if not self.spiele:
            self.befund.setHtml(
                "<p>Keine installierten Spiele gefunden.</p>"
                "<p>Gesucht wurde in Steams Bibliotheksdateien. Spiele außerhalb "
                "von Steam findet SPIELRaum noch nicht.</p>"
            )

    def _gewaehlt(self, zeile: int) -> None:
        if not 0 <= zeile < len(self.spiele):
            self.knopf_start.setEnabled(False)
            self.knopf_tasten.setEnabled(False)
            return
        spiel = self.spiele[zeile]
        self.knopf_start.setEnabled(True)
        # Der Tastenknopf gilt nur, wenn das Profil dieses Spiels überhaupt
        # eine Belegung mitbringt. Ein Knopf, der nichts tut, ist schlimmer
        # als keiner.
        p = profil.finden(steam_app_id=spiel.app_id)
        self.knopf_tasten.setEnabled(bool(p and p.tasten) or self.tasten_liegen)
        self.befund.setHtml(self._bericht(spiel))

    # --- Tasten -----------------------------------------------------------

    def _tasten_umschalten(self) -> None:
        """Belegung setzen oder zurücknehmen – ein Knopf für beides.

        Zwei getrennte Knöpfe wären ehrlicher gewesen, aber einer von beiden
        ist immer der falsche: Man kann nicht zweimal setzen und nicht
        zurücknehmen, was nicht liegt. Der Umschalter zeigt stattdessen an,
        was gerade gilt.
        """
        if self.tasten_liegen:
            meldung = tasten.zuruecknehmen()
            self.tasten_liegen = False
            self.knopf_tasten.setText("Belegung jetzt setzen")
            QMessageBox.information(self, "Tasten", meldung)
            return

        zeile = self.liste.currentRow()
        if not 0 <= zeile < len(self.spiele):
            return
        p = profil.finden(steam_app_id=self.spiele[zeile].app_id)
        if p is None or not p.tasten:
            QMessageBox.information(
                self, "Tasten",
                "Für dieses Spiel ist im Profil keine Tastenbelegung hinterlegt.")
            return

        # Ein Journal, damit auch diese Belegung zurückgenommen wird, wenn
        # SPIELRaum abstürzt, während sie liegt. Dieselbe Zusage wie beim
        # Start über das Programm.
        journal = zustand.Journal(spiel=f"{p.name} (nur Tasten)", pid=os.getpid())
        try:
            getan = tasten.setzen(p.tasten, journal)
        except tasten.TastenFehler as fehler:
            QMessageBox.warning(self, "Tasten gehen nicht", str(fehler))
            return

        zustand.schreiben(journal)
        self.tasten_liegen = True
        self.knopf_tasten.setText("Belegung zurücknehmen")
        QMessageBox.information(
            self, "Tasten umgelegt",
            f"{len(getan)} Zuordnungen gesetzt:\n\n" + "\n".join(getan)
            + "\n\nZum Zurücknehmen denselben Knopf noch einmal drücken.")

    # --- Der Bericht ------------------------------------------------------

    def _bericht(self, spiel: steam.Spiel) -> str:
        p = profil.finden(steam_app_id=spiel.app_id)
        dreht = umgebung.platte_dreht(spiel.ordner)
        umg = umgebung.ermitteln()

        teile = [f"<h2 style='color:{farben.GRAU_DUNKEL}'>{spiel.name}</h2>"]

        # --- Was vorliegt
        zeilen = [
            ("Größe", spiel.groesse_lesbar),
            ("Start", "Windows-Spiel unter Proton" if spiel.laeuft_unter_proton
                      else "nativ für Linux"),
            ("Datenträger", "<b style='color:#b4690e'>drehende Platte</b>" if dreht
                            else ("SSD" if dreht is False else "nicht feststellbar")),
            ("Ordner", f"<code>{spiel.ordner}</code>"),
        ]
        teile.append("<table cellpadding='3'>")
        for name, wert in zeilen:
            teile.append(f"<tr><td style='color:{farben.GRAU_LEISE}'>{name}</td>"
                         f"<td>{wert}</td></tr>")
        teile.append("</table>")

        if dreht:
            teile.append(
                f"<p style='background:#fff6e5;padding:8px;border-radius:5px'>"
                f"<b>Das ist der wahrscheinlichste Engpass.</b> Bei Road to Vostok "
                f"fiel die Ladezeit durch einen Umzug auf eine SSD von 23,8 auf "
                f"6,6 Sekunden, und die Nachladehänger verschwanden. Keine "
                f"Einstellung erreicht das.</p>"
            )

        # --- Das Profil
        teile.append(f"<h3 style='color:{farben.GRAU_DUNKEL}'>Profil</h3>")
        if p is None:
            teile.append(
                "<p>Für dieses Spiel gibt es noch kein Profil. SPIELRaum würde es "
                "unverändert starten.</p>"
            )
        else:
            was = []
            if p.nicht_stoeren and umg.hat("systemd-inhibit"):
                was.append("Bildschirmschoner und Ruhezustand bleiben weg")
            if p.gamemode and umg.hat("gamemoderun"):
                was.append("GameMode wird gerufen")
            if p.argumente:
                was.append("Startargumente: <code>" + " ".join(p.argumente) + "</code>")
            if p.variablen:
                was.append(f"{len(p.variablen)} Umgebungsvariable(n)")
            if p.mangohud and umg.hat("mangohud"):
                was.append("jeder Lauf wird gemessen")
            teile.append("<ul>" + "".join(f"<li>{z}</li>" for z in was) + "</ul>")
            for warnung in p.warnungen():
                teile.append(f"<p style='color:#b4690e'>{warnung}</p>")

            # --- Die Tastenbelegung dieses Spiels
            #
            # Steht hier und nicht hinter einem Knopf, weil es die Änderung
            # ist, die man beim Spielen tatsächlich merkt. Am 23.10.2026
            # zeigte der Befund alles -- Bildschirmschoner, GameMode,
            # Messung -- nur die elf Tastenzuordnungen nicht. Gefragt wurde
            # dann nach dem Knopf, nicht nach der Belegung.
            if p.tasten:
                teile.append(f"<h3 style='color:{farben.GRAU_DUNKEL}'>Tastenbelegung</h3>")
                bereit, grund = tasten.verfuegbar()
                teile.append(
                    "<p>Gilt nur, solange das Spiel läuft. Links steht, was du "
                    "drückst, rechts, was das Spiel sieht.</p>"
                )
                teile.append("<table cellpadding='3'>")
                for taste, ziel in p.tasten.items():
                    teile.append(
                        f"<tr><td style='color:{farben.GRAU_LEISE}'>"
                        f"<code>{_tastenname(taste)}</code></td>"
                        f"<td style='color:{farben.GRAU_LEISE}'>→</td>"
                        f"<td><code>{_tastenname(ziel)}</code></td></tr>"
                    )
                teile.append("</table>")
                if not bereit:
                    teile.append(
                        f"<p style='background:#fff6e5;padding:8px;border-radius:5px'>"
                        f"<b>Diese Belegung greift gerade nicht.</b><br>{grund}</p>"
                    )

                blatt = _tastenblatt(spiel)
                if blatt is not None:
                    teile.append(
                        f"<p>📄 <a href='file://{blatt}'>Tastenblatt öffnen</a> "
                        f"<span style='color:{farben.GRAU_LEISE}'>– die ganze "
                        f"Belegung samt Maus, zum Ausdrucken</span></p>"
                    )

        # --- Die Messungen
        teile.append(f"<h3 style='color:{farben.GRAU_DUNKEL}'>Messungen</h3>")
        ordner = stellschrauben.messordner() / str(spiel.app_id)
        laeufe = messen.laeufe(ordner)
        if not laeufe:
            teile.append(
                "<p>Noch nichts gemessen. Sobald das Spiel über SPIELRaum läuft, "
                "entsteht je Sitzung ein Protokoll.</p>"
            )
        else:
            teile.append("<table cellpadding='4'>")
            teile.append(f"<tr style='color:{farben.GRAU_LEISE}'><td>Lauf</td>"
                         "<td>Mittel</td><td>1-%-Tief</td><td>Laden</td></tr>")
            for lauf in laeufe[-6:]:
                k = messen.auswerten(lauf)
                if k is None:
                    teile.append(f"<tr><td>{lauf.name[4:14]}</td>"
                                 "<td colspan='3'>zu kurz für eine Aussage</td></tr>")
                    continue
                teile.append(
                    f"<tr><td>{lauf.name[4:]}</td><td><b>{k.mittel:.1f}</b></td>"
                    f"<td>{k.tief_1:.1f}</td><td>{k.ladezeit:.0f} s</td></tr>"
                )
            teile.append("</table>")
            teile.append(
                f"<p style='color:{farben.GRAU_LEISE};font-size:9pt'>"
                "Bildraten schwanken stark danach, wo im Spiel gemessen wurde – "
                "in einem Lauf wurden 30,9 bis 53,8 gemessen. Verlässlich ist "
                "vor allem die Ladezeit.</p>"
            )

        return "".join(teile)

    # --- Starten ----------------------------------------------------------

    def _starten(self) -> None:
        """Das Spiel über Steam starten, nicht direkt.

        Direkt zu starten wäre falsch: Dann fehlten die Steam-Laufzeit, das
        Overlay und – entscheidend – die Startoption, in der ``spielraum
        starten %command%`` steht. Über ``steam://rungameid/`` nimmt Steam
        den eingetragenen Weg, und SPIELRaum hängt sich dort ein, wo es
        hingehört.
        """
        zeile = self.liste.currentRow()
        if not 0 <= zeile < len(self.spiele):
            return
        spiel = self.spiele[zeile]

        if not umgebung.ermitteln().werkzeuge.get("steam") and not _steam_da():
            QMessageBox.warning(self, "Steam fehlt",
                                "Steam wurde nicht gefunden.")
            return

        p = profil.finden(steam_app_id=spiel.app_id)
        if p is None:
            antwort = QMessageBox.question(
                self, "Kein Profil",
                f"Für »{spiel.name}« gibt es kein Profil.\n\n"
                "Das Spiel startet dann unverändert. Trotzdem starten?",
            )
            if antwort != QMessageBox.Yes:
                return

        subprocess.Popen(["steam", f"steam://rungameid/{spiel.app_id}"],
                         start_new_session=True)


def _steam_da() -> bool:
    import shutil
    return shutil.which("steam") is not None


def main() -> int:
    anwendung = QApplication([])
    anwendung.setApplicationName("SPIELRaum")
    fenster = Fenster()
    fenster.show()
    return anwendung.exec()


if __name__ == "__main__":
    raise SystemExit(main())
