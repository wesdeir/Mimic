"""
MIMIC v4.0 -- adaptive human-like clicking engine.

Entry point only. The implementation lives in the `mimic` package:
    mimic/config.py   configuration, risk assessment, presets
    mimic/engine.py   Markov state model and delay generation
    mimic/session.py  session persistence, human click capture
    mimic/widgets.py  canvas graph widgets
    mimic/gui.py      main application window
"""

import sys

from mimic.gui import MinecraftAutoClickerGUI


BANNER = """
    ═══════════════════════════════════════════════════════════════════════
    
            ███╗   ███╗██╗███╗   ███╗██╗ ██████╗
            ████╗ ████║██║████╗ ████║██║██╔════╝
            ██╔████╔██║██║██╔████╔██║██║██║     
            ██║╚██╔╝██║██║██║╚██╔╝██║██║██║     
            ██║ ╚═╝ ██║██║██║ ╚═╝ ██║██║╚██████╗
            ╚═╝     ╚═╝╚═╝╚═╝     ╚═╝╚═╝ ╚═════╝
                                                    
                             v4.0.0
    
    ═══════════════════════════════════════════════════════════════════════
    
         LAUNCH SEQUENCE
       • Loading adaptive engine...
       • Initializing statistical distributions...
       • Starting GUI...
    
    ═══════════════════════════════════════════════════════════════════════
"""


def main():
    # Windows consoles default to cp1252 when stdout is redirected, which
    # cannot encode the box-drawing art below. Degrade instead of crashing.
    try:
        print(BANNER)
    except UnicodeEncodeError:
        print(BANNER.encode('ascii', 'replace').decode('ascii'))
    MinecraftAutoClickerGUI().run()


if __name__ == "__main__":
    sys.exit(main())
