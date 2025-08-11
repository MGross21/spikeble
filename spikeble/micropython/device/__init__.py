"The `device` module enables you to write code to get information about devices plugged into the hub."


async def data(port: int) -> tuple[int]:
    "Retrieve the raw LPF-2 data from a device."
    assert port in range(6), "Invalid port"


async def id(port: int) -> int:
    "Retrieve the device id of a device. Each device has an id based on its type."
    assert port in range(6), "Invalid port"


async def get_duty_cycle(port: int) -> int:
    "Retrieve the duty cycle for a device. Returned values is in range 0 to 10000"
    assert port in range(6), "Invalid port"


async def ready(port: int) -> bool:
    "When a device is attached to the hub it might take a short amount of time before it's ready to accept requests. Use `ready` to test for the readiness of the attached devices."
    assert port in range(6), "Invalid port"


async def set_duty_cycle(port: int, duty_cycle: int) -> None:
    "Set the duty cycle for a device. Accepted values are in range 0 to 10000."
    assert port in range(6), "Invalid port"
    assert duty_cycle in range(10001), "Invalid duty cycle"
