"""
The `force_sensor` module contains all functions and constants to use the Force Sensor.

To use the Force Sensor module add the following import statement to your project:

>>> import force_sensor

All functions in the module should be called inside the force_sensor module as a prefix like so:

>>> force_sensor.force(port.A)
"""


async def force(port: int) -> int:
    """
    Retrieves the measured force in decinewtons (0 to 100).

    Example
    -------
    >>> from hub import port
    >>> import force_sensor
    >>> print(force_sensor.force(port.A))

    Parameters
    ----------
    port : int
        A port from the `port` submodule in the hub module.
    """
    assert port in range(6), "Invalid port"


async def pressed(port: int) -> bool:
    """
    Tests whether the button on the sensor is pressed. Returns true if the force sensor connected to port is pressed.

    Example
    -------
    >>> from hub import port
    >>> import force_sensor
    >>> print(force_sensor.pressed(port.A))

    Parameters
    ----------
    port : int
        A port from the `port` submodule in the hub module.
    """
    assert port in range(6), "Invalid port"


async def raw(port: int) -> int:
    """
    Returns the raw, uncalibrated force value of the force sensor connected on `port`.

    Example
    -------
    >>> from hub import port
    >>> import force_sensor
    >>> print(force_sensor.raw(port.A))

    Parameters
    ----------
    port : int
        A port from the `port` submodule in the hub module.
    """
    assert port in range(6), "Invalid port"
