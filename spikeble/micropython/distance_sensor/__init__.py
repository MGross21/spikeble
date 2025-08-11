"""The distance_sensor module enables you to write code that reacts to specific distances or light up the Distance Sensor in different ways."""

async def clear(port: int) -> None:
    "Turns off all the lights in the Distance Sensor connected to `port`."
    assert port in range(6), "Invalid port"
async def distance(port: int) -> int:
    "Retrieve the distance in millimeters captured by the Distance Sensor connected to `port`. If the Distance Sensor cannot read a valid distance it will return -1."
    assert port in range(6), "Invalid port"
async def get_pixel(port: int, x: int, y: int) -> int:
    "Retrieve the intensity of a specific light on the Distance Sensor connected to `port`."
    assert port in range(6), "Invalid port"
    assert x in range(4), "Invalid x coordinate"
    assert y in range(4), "Invalid y coordinate"
async def set_pixel(port: int, x: int, y: int, intensity: int) -> None:
    "Changes the intensity of a specific light on the Distance Sensor connected to `port`."
    assert port in range(6), "Invalid port"
    assert x in range(4), "Invalid x coordinate"
    assert y in range(4), "Invalid y coordinate"
async def show(port: int, pixels: list[int]) -> None:
    "Change all the lights at the same time."
    assert port in range(6), "Invalid port"