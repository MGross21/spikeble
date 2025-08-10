# control.py
from lib.enumeration import HubPort
from .hub import Hub

def _port_name(p):  # accept enum or 'A'..'F'
    return p.name if isinstance(p, HubPort) else str(p)

async def motor_run_degrees(hub: Hub, *, port: HubPort|str, degrees: int, speed: int, slot: int = 1):
    code = f"""
from spike import Motor
m = Motor('{_port_name(port)}')
m.run_for_degrees(degrees={degrees}, speed={speed})
"""
    await hub.run_source(slot=slot, name="motor.py", source=code)

async def motor_start_stop(hub: Hub, *, port: HubPort|str, speed: int, seconds: float, slot: int = 1):
    code = f"""
from spike import Motor
from time import sleep
m = Motor('{_port_name(port)}')
m.start(speed={speed})
sleep({seconds})
m.stop()
"""
    await hub.run_source(slot=slot, name="motor_run.py", source=code)

async def motor_to_position(hub: Hub, *, port: HubPort|str, position: int, speed: int, slot: int = 1):
    code = f"""
from spike import Motor
m = Motor('{_port_name(port)}')
m.run_to_position(position={position}, speed={speed})
"""
    await hub.run_source(slot=slot, name="motor_pos.py", source=code)
