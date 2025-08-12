from typing import Callable

async def run_fn(
    program: Callable,
    *,
    slot: int = 0,
    stay_connected: bool = False,
):
    from .spike import logger
    from ._utils import func_to_string
    try:
        # call function and see if any front-side errors trigger
        program()
    except Exception as e:
        logger.error(f"Error occurred while running program: {e}")
    await run_str(
        func_to_string(program),
        slot=slot,
        name=program.__name__ + ".py",
        stay_connected=stay_connected
    )

run = run_fn # shorthand alias default

async def run_file(
    program_path: str,
    *,
    slot: int = 0,
    stay_connected: bool = False,
):
    from .spike import logger
    from pathlib import Path
    if not Path(program_path).exists():
        logger.error(f"File not found: {program_path}")
        return

    program_str = Path(program_path).read_text()
    try:
        compile(program_str, program_path, "exec")
    except Exception as e:
        logger.error(f"Error compiling {program_path}: {e}")
        return
    await run_str(
        program_str,
        slot=slot,
        name=Path(program_path).name,
        stay_connected=stay_connected
    )

async def run_str(
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
        await hub.upload_program(program_str.encode("utf-8"), name=name)
        await hub.start_program()
        if stay_connected:
            try:
                await hub.run_until_disconnect()
            except KeyboardInterrupt:
                await hub.disconnect()