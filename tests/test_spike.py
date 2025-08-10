import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from pathlib import Path
from spike.spike import run

PROGRAM = Path(os.path.join(os.path.dirname(__file__), "__test.py")).read_bytes()

if __name__ == "__main__":
    asyncio.run(run(PROGRAM))
