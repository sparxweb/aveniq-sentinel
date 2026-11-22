"""NeuralShield AI — Package Dashboard Entrypoint.

Allows launching the Cybersecurity Command Center directly via:
    python -m streamlit run src/neuralshield/dashboard.py
or:
    streamlit run src/neuralshield/dashboard.py
"""

import sys
from pathlib import Path

# Add project root and src to path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SRC_DIR = ROOT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Import main application routine from app.py
from app import main

if __name__ == "__main__":
    main()
