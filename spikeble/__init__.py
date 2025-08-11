from typing import Callable

async def run_fn(
    program: Callable,
    *,
    slot: int = 0,
    name: str = "program.py",
    stay_connected: bool = False,
):
    from .spike import logger
    from ._utils import func_to_string
    try:
        # call function and see if any front-side errors trigger
        program()
    except Exception as e:
        logger.error(f"Error occurred while running program: {e}")
    await run_string(
        func_to_string(program),
        slot=slot,
        name=name,
        stay_connected=stay_connected
    )

run = run_fn # shorthand alias default

async def run_file(
    program: Callable,
    *,
    slot: int = 0,
    name: str = "program.py",
    stay_connected: bool = False,
):
    from .spike import logger
    from ._utils import func_to_string
    from pathlib import Path
    if not Path(name).exists():
        logger.error(f"File not found: {name}")
        return
    await run_string(
        Path(name).read_bytes(),
        slot=slot,
        name=name,
        stay_connected=stay_connected
    )

async def run_string(
    program_str: str,
    *,
    slot: int = 0,
    name: str = "program.py",
    stay_connected: bool = False,
):
    from .spike import Spike
    async with Spike(timeout=10, slot=slot) as hub:
        await hub.get_info()
        await hub.enable_notifications()
        await hub.clear_slot()
        await hub.upload_program(program_str, name=name)
        await hub.start_program()
        if stay_connected:
            await hub.run_until_disconnect()