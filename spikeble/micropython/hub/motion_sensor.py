"""
To use the Motion Sensor module, add the following import statement to your project:

>>> from hub import motion_sensor

All functions in the module should be called using the `motion_sensor` module as a prefix, for example:

>>> motion_sensor.up_face()
"""

TOP = 0
"""The SPIKE Prime hub face with the Light Matrix."""
FRONT = 1
"""The SPIKE Prime hub face where the speaker is."""
RIGHT = 2
"""The right side of the SPIKE Prime hub when facing the front hub face."""
BOTTOM = 3
"""The side of the SPIKE Prime hub where the battery is."""
BACK = 4
"""The SPIKE Prime hub face with the USB charging port."""
LEFT = 5
"""The left side of the SPIKE Prime hub when facing the front hub face."""


def acceleration(raw_unfiltered: bool) -> tuple[int, int, int]:
    """
    Returns a tuple containing x, y & z acceleration values as integers. The values are mili G, so 1 / 1000 G

    Parameters
    ----------
    raw_unfiltered : bool
        If we want the data back raw and unfiltered
    """
    pass


def angular_velocity(raw_unfiltered: bool) -> tuple[int, int, int]:
    """
    Returns a tuple containing x, y & z angular velocity values as integers. The values are decidegrees per second

    Parameters
    ----------
    raw_unfiltered : bool
        If we want the data back raw and unfiltered
    """
    pass


def gesture() -> int:
    """
    Returns the gesture recognized.

    Possible values are:
    - `motion_sensor.TAPPED`
    - `motion_sensor.DOUBLE_TAPPED`
    - `motion_sensor.SHAKEN`
    - `motion_sensor.FALLING`
    - `motion_sensor.UNKNOWN`
    """
    pass


def get_yaw_face() -> int:
    """
    Retrieve the face of the hub that yaw is relative to.

    If you place the hub on a flat surface with the returned face pointing up, only the yaw value will update as you rotate the hub.

    Returns
    -------
    int
        One of the following constants indicating the hub face:
        - `motion_sensor.TOP`: The SPIKE Prime hub face with the USB charging port.
        - `motion_sensor.FRONT`: The SPIKE Prime hub face with the Light Matrix.
        - `motion_sensor.RIGHT`: The right side of the SPIKE Prime hub when facing the front hub face.
        - `motion_sensor.BOTTOM`: The side of the SPIKE Prime hub where the battery is.
        - `motion_sensor.BACK`: The SPIKE Prime hub face where the speaker is.
        - `motion_sensor.LEFT`: The left side of the SPIKE Prime hub when facing the front hub face.
    """
    pass


def quaternion() -> tuple[float, float, float, float]:
    """Returns the hub orientation quaternion as a tuple[w: float, x: float, y: float, z: float]."""
    pass


def reset_tap_count() -> None:
    """Reset the tap count returned by the `tap_count` function."""
    pass


def reset_yaw(angle: int) -> None:
    """Change the yaw angle offset. The angle set will be the new yaw value."""
    pass


def set_yaw_face(up: int) -> bool:
    """
    Change what hub face is used as the yaw face. If you put the hub on a flat surface with this face pointing up, when you rotate the hub only the yaw will update.

    Parameters
    ----------

    up: int
        The hub face that should be set as the upwards facing hub face.
        Available values are:

        - `motion_sensor.TOP` The SPIKE Prime hub face with the USB charging port.
        - `motion_sensor.FRONT` The SPIKE Prime hub face with the Light Matrix.
        - `motion_sensor.RIGHT` The right side of the SPIKE Prime hub when facing the front hub face.
        - `motion_sensor.BOTTOM` The side of the SPIKE Prime hub where the battery is.
        - `motion_sensor.BACK` The SPIKE Prime hub face where the speaker is.
        - `motion_sensor.LEFT` The left side of the SPIKE Prime hub when facing the front hub face.
    """
    pass


def stable() -> bool:
    """Whether or not the hub is resting flat."""
    pass


def tap_count() -> int:
    """Returns the number of taps recognized since the program started or last time `motion_sensor.reset_tap_count()` was called."""
    pass


def tilt_angles() -> tuple[int, int, int]:
    """Returns a tuple containing yaw pitch and roll values as integers. Values are decidegrees"""
    pass


def up_face() -> int:
    """
    Returns the Hub face that is currently facing up
    - `motion_sensor.TOP` The SPIKE Prime hub face with the USB charging port.
    - `motion_sensor.FRONT` The SPIKE Prime hub face with the Light Matrix.
    - `motion_sensor.RIGHT` The right side of the SPIKE Prime hub when facing the front hub face.
    - `motion_sensor.BOTTOM` The side of the SPIKE Prime hub where the battery is.
    - `motion_sensor.BACK` The SPIKE Prime hub face where the speaker is.
    - `motion_sensor.LEFT` The left side of the SPIKE Prime hub when facing the front hub face."""
