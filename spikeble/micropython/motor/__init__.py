"""
To use a Motor add the following import statement to your project:

>>> import motor

All functions in the module should be called inside the motor module as a prefix like so:

>>> motor.run(port.A, 1000)
"""

from typing import Awaitable

READY = 0
RUNNING = 1
STALLED = 2
CANCELLED = 3
ERROR = 4
DISCONNECTED = 5

COAST = 0
BRAKE = 1
HOLD = 2
CONTINUE = 3
SMART_COAST = 4
SMART_BRAKE = 5

CLOCKWISE = 0
COUNTERCLOCKWISE = 1
SHORTEST_PATH = 2
LONGEST_PATH = 3


def absolute_position(port: int) -> int:
    """
    Get the absolute position of a Motor

    Parameters
    ----------
    port : int
        A port from the `port` submodule in the `hub` module
    """
    assert port in range(6), "Invalid port"


def get_duty_cycle(port: int) -> int:
    """
    Get the pwm of a Motor

    Parameters
    ----------
    port : int
        A port from the `port` submodule in the `hub` module
    """
    assert port in range(6), "Invalid port"


def relative_position(port: int) -> int:
    """
    Get the relative position of a Motor

    Parameters
    ----------
    port : int
        A port from the `port` submodule in the `hub` module
    """
    assert port in range(6), "Invalid port"


def reset_relative_position(port: int, position: int) -> None:
    """
    Reset the relative position of a Motor

    Parameters
    ----------
    port : int
        A port from the `port` submodule in the `hub` module
    position : int
        The degree of the motor
    """
    assert port in range(6), "Invalid port"
    assert isinstance(position, int), "Position must be an integer"


def run(port: int, velocity: int, *, acceleration: int = 1000) -> None:
    """
    Start a Motor at a constant speed

    Example
    --------
    ```python
    from hub import port
    import motor, time

    # Start motor
    motor.run(port.A, 1000)
    ```

    Parameters
    ----------
    port : int
        A port from the `port` submodule in the `hub` module
    velocity : int
        The velocity in degrees/sec

        Value ranges depends on motor type.

        - Small motor (essential): -660 to 660
        - Medium motor: -1110 to 1110
        - Large motor: -1050 to 1050

    acceleration : int
        The acceleration (deg/sec²) (1 - 10000)
    """
    assert port in range(6), "Invalid port"
    assert -10_000 <= velocity <= 10_000, "Invalid velocity"
    assert 1 <= acceleration <= 10_000, "Invalid acceleration"


async def run_for_degrees(
    port: int,
    degrees: int,
    velocity: int,
    *,
    stop: int = BRAKE,
    acceleration: int = 1000,
    deceleration: int = 1000,
) -> Awaitable:
    """
    Turn a motor for a specific number of degrees. When awaited returns a status of the movement that corresponds to one of the following constants:

    - `motor.READY`
    - `motor.RUNNING`
    - `motor.STALLED`
    - `motor.CANCELLED`
    - `motor.ERROR`
    - `motor.DISCONNECTED`

    Parameters
    ----------
    port : int
        A port from the `port` submodule in the `hub` module
    degrees : int
        The number of degrees
    velocity : int
        The velocity in degrees/sec

        Value ranges depends on motor type.

        - Small motor (essential): -660 to 660
        - Medium motor: -1110 to 1110
        - Large motor: -1050 to 1050
    stop : int
        The behavior of the Motor after it has stopped. Use the constants in the motor module.

        Possible values are
        - `motor.COAST` to make the motor coast until a stop
        - `motor.BRAKE` to brake and continue to brake after stop
        - `motor.HOLD` to tell the motor to hold it's position
        - `motor.CONTINUE` to tell the motor to keep running at whatever velocity it's running at until it gets another command
        - `motor.SMART_COAST` to make the motor brake until stop and then coast and compensate for inaccuracies in the next command
        - `motor.SMART_BRAKE` to make the motor brake and continue to brake after stop and compensate for inaccuracies in the next command
    acceleration : int
        The acceleration (deg/sec²) (1 - 10000)
    deceleration : int
        The deceleration (deg/sec²) (1 - 10000)
    """
    assert port in range(6), "Invalid port"
    assert isinstance(degrees, int), "Degrees must be an integer"
    assert -10_000 <= velocity <= 10_000, "Invalid velocity"
    assert stop in (COAST, BRAKE, HOLD, CONTINUE, SMART_COAST, SMART_BRAKE), (
        "Invalid stop behavior"
    )
    assert 1 <= acceleration <= 10_000, "Invalid acceleration"
    assert 1 <= deceleration <= 10_000, "Invalid deceleration"


async def run_for_time(
    port: int,
    duration: int,
    velocity: int,
    *,
    stop: int = BRAKE,
    acceleration: int = 1000,
    deceleration: int = 1000,
) -> Awaitable:
    """
    Run a Motor for a limited amount of time. When awaited returns a status of the movement that corresponds to one of the following constants:

    - `motor.READY`
    - `motor.RUNNING`
    - `motor.STALLED`
    - `motor.ERROR`
    - `motor.DISCONNECTED`

    Example
    -------
    ```python
    from hub import port
    import runloop
    import motor

    async def main():
        # Run at 1000 velocity for 1 second
        await motor.run_for_time(port.A, 1000, 1000)

        # Run at 280 velocity for 1 second
        await motor_pair.run_for_time(port.A, 1000, 280)

        # Run at 280 velocity for 10 seconds with a slow deceleration
        await motor_pair.run_for_time(port.A, 10000, 280, deceleration=10)

    runloop.run(main())
    ```

    Parameters
    ----------
    port : int
        A port from the `port` submodule in the `hub` module
    duration : int
        The duration in milliseconds
    velocity : int
        The velocity in degrees/sec

        Value ranges depends on motor type.

        - Small motor (essential): -660 to 660
        - Medium motor: -1110 to 1110
        - Large motor: -1050 to 1050
    direction : int
        The direction to turn.
        Options are:

        - `motor.CLOCKWISE`
        - `motor.COUNTERCLOCKWISE`
        - `motor.SHORTEST_PATH`
        - `motor.LONGEST_PATH`
    stop : int
        The behavior of the Motor after it has stopped. Use the constants in the motor module.

        Possible values are
        - `motor.COAST` to make the motor coast until a stop
        - `motor.BRAKE` to brake and continue to brake after stop
        - `motor.HOLD` to tell the motor to hold it's position
        - `motor.CONTINUE` to tell the motor to keep running at whatever velocity it's running at until it gets another command
        - `motor.SMART_COAST` to make the motor brake until stop and then coast and compensate for inaccuracies in the next command
        - `motor.SMART_BRAKE` to make the motor brake and continue to brake after stop and compensate for inaccuracies in the next command
    acceleration : int
        The acceleration (deg/sec²) (1 - 10000)
    deceleration : int
        The deceleration (deg/sec²) (1 - 10000)
    """
    assert port in range(6), "Invalid port"
    assert stop in (COAST, BRAKE, HOLD, CONTINUE, SMART_COAST, SMART_BRAKE), (
        "Invalid stop behavior"
    )
    assert -10_000 <= velocity <= 10_000, "Invalid velocity"
    assert 1 <= acceleration <= 10_000, "Invalid acceleration"
    assert 1 <= deceleration <= 10_000, "Invalid deceleration"


async def run_to_absolute_position(
    port: int,
    position: int,
    velocity: int,
    *,
    direction: int = SHORTEST_PATH,
    stop: int = BRAKE,
    acceleration: int = 1000,
    deceleration: int = 1000,
) -> Awaitable:
    """
    Turn a motor to an absolute position. When awaited returns a status of the movement that corresponds to one of the following constants:

    - `motor.READY`
    - `motor.RUNNING`
    - `motor.STALLED`
    - `motor.CANCELED`
    - `motor.ERROR`
    - `motor.DISCONNECTED`

    Parameters
    ----------
    port : int
        A port from the `port` submodule in the `hub` module
    position : int
        The target position in degrees
    velocity : int
        The velocity in degrees/sec

        Value ranges depends on motor type.

        - Small motor (essential): -660 to 660
        - Medium motor: -1110 to 1110
        - Large motor: -1050 to 1050
    direction : int
        The direction to turn the motor. Use the constants in the motor module.

        Possible values are
        - `motor.CLOCKWISE`
        - `motor.COUNTERCLOCKWISE`
        - `motor.SHORTEST_PATH`
        - `motor.LONGEST_PATH`
    stop : int
        The behavior of the Motor after it has stopped. Use the constants in the motor module.

        Possible values are
        - `motor.COAST` to make the motor coast until a stop
        - `motor.BRAKE` to brake and continue to brake after stop
        - `motor.HOLD` to tell the motor to hold it's position
        - `motor.CONTINUE` to tell the motor to keep running at whatever velocity it's running at until it gets another command
        - `motor.SMART_COAST` to make the motor brake until stop and then coast and compensate for inaccuracies in the next command
        - `motor.SMART_BRAKE` to make the motor brake and continue to brake after stop and compensate for inaccuracies in the next command
    acceleration : int
        The acceleration (deg/sec²) (1 - 10000)
    deceleration : int
        The deceleration (deg/sec²) (1 - 10000)
    """
    assert port in range(6), "Invalid port"
    assert direction in (
        CLOCKWISE,
        COUNTERCLOCKWISE,
        SHORTEST_PATH,
        LONGEST_PATH,
    ), "Invalid direction"
    assert stop in (COAST, BRAKE, HOLD, CONTINUE, SMART_COAST, SMART_BRAKE), (
        "Invalid stop behavior"
    )
    assert -10_000 <= velocity <= 10_000, "Invalid velocity"
    assert 1 <= acceleration <= 10_000, "Invalid acceleration"
    assert 1 <= deceleration <= 10_000, "Invalid deceleration"


def set_duty_cycle(port: int, pwm: int) -> None:
    """
    Set the duty cycle of a motor.

    Parameters
    ----------
    port : int
        A port from the `port` submodule in the `hub` module
    pwm : int
        The PWM value (-10000-10000)
    """
    assert port in range(6), "Invalid port"
    assert -10_000 <= pwm <= 10_000, "Invalid PWM"


def stop(port: int, *, stop: int = BRAKE) -> None:
    """
    Stop a motor.

    Example
    -------
    ```python
    from hub import port
    import motor, time

    # Start motor
    motor.run(port.A, 1000)

    # Wait for 2 seconds
    time.sleep_ms(2000)

    # Stop motor
    motor.stop(port.A)
    ```

    Parameters
    ----------
    port : int
        A port from the `port` submodule in the `hub` module
    stop : int
        The stop behavior. Use the constants in the motor module.

        Possible values are
        - `motor.COAST` to make the motor coast until a stop
        - `motor.BRAKE` to brake and continue to brake after stop
        - `motor.HOLD` to tell the motor to hold it's position
        - `motor.CONTINUE` to tell the motor to keep running at whatever velocity it's running at until it gets another command
        - `motor.SMART_COAST` to make the motor brake until stop and then coast and compensate for inaccuracies in the next command
        - `motor.SMART_BRAKE` to make the motor brake and continue to brake after stop and compensate for inaccuracies in the next command
    """
    assert port in range(6), "Invalid port"
    assert stop in (COAST, BRAKE, HOLD, CONTINUE, SMART_COAST, SMART_BRAKE), (
        "Invalid stop behavior"
    )


def velocity(port: int) -> int:
    """
    Get the velocity (deg/sec) of a Motor

    Parameters
    ----------
    port : int
        A port from the `port` submodule in the `hub` module
    """
    assert port in range(6), "Invalid port"
