import asyncio
from typing import Callable

async def run(program: Callable, slot: int = 0, name: str = "program.py", stay_connected: bool = False):

    try:
        program()
    except Exception as e:
        logger.error(f"Error occurred while running program: {e}")
    else:
        from .spike import Spike, logger
        from ._utils import func_to_string
    program_str = func_to_string(program)
    async with Spike(timeout=10, slot=slot) as hub:
        await asyncio.gather(
            hub.get_info(),
            hub.enable_notifications(),
            hub.clear_slot()
        )
        await hub.upload_program(program_str, name=name)
        await hub.start_program()
        if stay_connected:
            await hub.run_until_disconnect()