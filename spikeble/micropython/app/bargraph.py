"The bargraph module is used make bar graphs in the SPIKE App"

from typing import Awaitable


def change(color: int, value: float) -> None:
    assert 0 <= color <= 10, "Color must be between 0 and 10"
    assert 0 <= value <= 100, "Value must be between 0 and 100"


def clear_all() -> None:
    pass


async def get_value(color: int) -> Awaitable:
    pass


def set_value(color: int, value: float) -> None:
    pass


def show(fullscreen: bool) -> None:
    pass
