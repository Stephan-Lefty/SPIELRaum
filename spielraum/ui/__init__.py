"""Die grafische Oberfläche von SPIELRaum.

Bewusst getrennt vom Kern: ``spielraum.ui`` darf ``spielraum.profil``,
``spielraum.steam`` und ``spielraum.messen`` benutzen, aber niemals
umgekehrt. Die Kommandozeile muss ohne PySide6 vollständig funktionieren –
auf einem Server, in der CI, in einer Textkonsole.

**PySide6 kommt aus der Distribution, nicht aus PyPI.** Sowohl Debian 13 als
auch Arch führen es in den Paketquellen, und die dortigen Fassungen sind
gegen das jeweilige Qt gebaut. Ein über pip nachgezogenes PySide6 bringt sein
eigenes Qt mit – 150 MB, die sich mit dem System beißen können. Deshalb legt
``install.sh`` das venv mit ``--system-site-packages`` an.
"""

from __future__ import annotations


def verfuegbar() -> tuple[bool, str]:
    """Lässt sich die Oberfläche überhaupt starten?

    Gibt einen Wahrheitswert und eine Erklärung zurück. Die Erklärung nennt
    den Installationsbefehl der jeweiligen Distribution – eine Meldung wie
    »ModuleNotFoundError: PySide6« hilft niemandem weiter.
    """
    try:
        import PySide6  # noqa: F401
    except ImportError:
        from .. import umgebung

        umg = umgebung.ermitteln()
        if umg.familie == "arch":
            return False, ("Die Oberfläche braucht PySide6. Nachinstallieren mit:\n"
                           "    sudo pacman -S pyside6")
        if umg.familie == "debian":
            return False, ("Die Oberfläche braucht PySide6. Nachinstallieren mit:\n"
                           "    sudo apt install python3-pyside6.qtwidgets")
        return False, "Die Oberfläche braucht PySide6 (Paket je nach System verschieden)."
    return True, ""
