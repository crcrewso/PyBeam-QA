"""Unit tests: no Qt, no display. They run from the repository root like the GUI tests."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
