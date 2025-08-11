def clear(port: int) -> None:
    "Turn off all pixels on a Color Matrix"
    assert port in range(6), "Invalid port"


def get_pixel(port: int, x: int, y: int) -> tuple[int, int]:
    "Retrieve a specific pixel represented as a tuple containing the color and intensity"
    assert port in range(6), "Invalid port"


def set_pixel(port: int, x: int, y: int, pixel: tuple[int, int]) -> None:
    "Change a single pixel on a Color Matrix"
    assert port in range(6), "Invalid port"


def show(port: int, pixels: list[tuple[int, int]]) -> None:
    "Change all pixels at once on a Color Matrix"
    assert port in range(6), "Invalid port"
