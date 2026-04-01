import sys
from pathlib import Path

# Make mazegen directory importable as a module
sys.path.insert(0, str(Path(__file__).parent / "mazegen"))
