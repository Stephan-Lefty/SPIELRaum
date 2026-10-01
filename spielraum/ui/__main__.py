"""Damit ``python -m spielraum.ui.fenster`` und ``python -m spielraum.ui``
beide funktionieren – der Starter aus install.sh nimmt den ersten Weg.
"""

from .fenster import main

if __name__ == "__main__":
    raise SystemExit(main())
