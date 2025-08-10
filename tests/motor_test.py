import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
from spike.hub.hub import Hub
from spike.hub.motor import motor_run_degrees, motor_start_stop, motor_to_position
from lib.enumeration import HubPort

async def main():
    async with Hub() as hub:
        await hub.get_info()
        await motor_run_degrees(hub, port=HubPort.A, degrees=360, speed=50)
        await motor_start_stop(hub, port='B', speed=60, seconds=1.5)
        await motor_to_position(hub, port='C', position=90, speed=30)

asyncio.run(main())
