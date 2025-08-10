# Add package link
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "spike"))

# Main Code
import asyncio
import os
from pathlib import Path
from spike import run

PROGRAM = Path(os.path.join(os.path.dirname(__file__), "__test.py")).read_bytes()

if __name__ == "__main__":
    asyncio.run(run(PROGRAM))
