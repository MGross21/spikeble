import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))




# example.py
import asyncio
from pathlib import Path
from spike.spike import Spike, run

EXAMPLE_SLOT = 0
PROGRAM = Path(os.path.join(os.path.dirname(__file__), "__test.py")).read_bytes()

async def main():
    await run(PROGRAM)

if __name__ == "__main__":
    asyncio.run(main())
