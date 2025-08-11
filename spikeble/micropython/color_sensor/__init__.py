"The `color_sensor` module enables you to write code that reacts to specific colors or the intensity of the reflected light."


async def color(port: int) -> int:
    "Returns the color value of the detected color. Use the `color` module to map the color value to a specific color."
    assert port in range(6), "Invalid port"


async def reflection(port: int) -> int:
    "Retrieves the intensity of the reflected light (0-100%)."
    assert port in range(6), "Invalid port"


async def rgbi(port: int) -> tuple[int, int, int, int]:
    "Retrieves the overall color intensity and intensity of red, green and blue."
    assert port in range(6), "Invalid port"
