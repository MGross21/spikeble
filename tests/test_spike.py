import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))




# example.py
import asyncio
from pathlib import Path
from spike.spike import Spike

EXAMPLE_SLOT = 0
PROGRAM = Path(os.path.join(os.path.dirname(__file__), "__test.py")).read_bytes()

async def main():
    async with Spike(timeout=10, slot=EXAMPLE_SLOT) as hub:
        await hub.get_info()
        await hub.enable_notifications()
        await hub.clear_slot()
        await hub.upload_program(PROGRAM, name="program.py")
        await hub.start_program()
        await hub.run_until_disconnect()

if __name__ == "__main__":
    asyncio.run(main())
