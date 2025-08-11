import spikeble
import asyncio
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent / "_ex1.py"

if __name__ == "__main__":
    asyncio.run(spikeble.run_file(SCRIPT_DIR))
