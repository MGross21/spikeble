import spikeble
import asyncio
from pathlib import Path

if __name__ == "__main__":
    asyncio.run(spikeble.run_file(
        str((Path(__file__).parent / "_ex1.py").resolve())
    ))
