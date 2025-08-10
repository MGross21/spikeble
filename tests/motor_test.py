# test_control.py - Fixed test suite for LEGO SPIKE Prime
import os
import sys


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
from spike.hub.hub import Hub
from spike.hub.motor import Motor
from spike.lib.enumeration import MotorDeviceType, HubPort


async def test_motor_degrees():
    async with Hub() as hub:
        motor = Motor(port=HubPort.A, type=MotorDeviceType.SMALL)
        await motor.run_for_degrees(hub, degrees=90, velocity=100)

if __name__ == "__main__":
    asyncio.run(test_motor_degrees())