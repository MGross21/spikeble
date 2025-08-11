from typing import Awaitable


async def play(
    sound_name: str, volume: int = 100, pitch: int = 0, pan: int = 0
) -> Awaitable:
    """Play a sound in the SPIKE App"""
    assert 0 <= volume <= 100, "Volume must be between 0 and 100"
    assert -100 <= pan <= 100, "Pan must be between -100 and 100"


def set_attributes(volume: int, pitch: int, pan: int) -> None:
    assert 0 <= volume <= 100, "Volume must be between 0 and 100"
    assert -100 <= pan <= 100, "Pan must be between -100 and 100"


def stop() -> None:
    pass
