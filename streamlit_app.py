"""NeuralShield AI — Entrypoint Alias.

Delegates directly to app.py to maintain zero duplication.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app import main

if __name__ == "__main__":
    main()
