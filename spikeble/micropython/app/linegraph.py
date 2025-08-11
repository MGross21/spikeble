"The linegraph module is used make line graphs in the SPIKE App"

from typing import Awaitable

def clear(color: int) -> None:
    assert 0 <= color <= 10, "Color must be between 0 and 10"
def clear_all() -> None: pass
async def get_average(color: int) -> Awaitable:
    assert 0 <= color <= 10, "Color must be between 0 and 10"
async def get_last(color: int) -> Awaitable:
    assert 0 <= color <= 10, "Color must be between 0 and 10"
async def get_max(color: int) -> Awaitable:
    assert 0 <= color <= 10, "Color must be between 0 and 10"
async def get_min(color: int) -> Awaitable:
    assert 0 <= color <= 10, "Color must be between 0 and 10"
def hide() -> None: pass
def plot(color: int, x: float, y: float) -> None:
    assert 0 <= color <= 10, "Color must be between 0 and 10"
def show(fullscreen: bool) -> None: pass