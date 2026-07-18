"""Make the repo root importable so tests can `import narrate_book`, etc.,
without the project needing a src-layout or a build step.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
