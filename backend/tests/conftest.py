import sys
from pathlib import Path

# Add backend directory to PYTHONPATH for module imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
