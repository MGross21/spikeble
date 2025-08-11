"""
The `runloop` module contains all functions and constants to use the Runloop.

To use the Runloop module add the following import statement to your project:


>>> import runloop

All functions in the module should be called inside the `runloop` module as a prefix like so:

>>> runloop.run(some_async_function())
"""

from typing import Awaitable, Callable


def run(*functions: Awaitable) -> None:
    """
    Start any number of parallel `async` functions. This is the function you should use to create programs with a similar structure to Word Blocks.

    Parameters
    ----------
    functions : Awaitable
        The functions to run
    """
    pass


async def sleep_ms(duration: int) -> Awaitable:
    """
    Pause the execution of the application for any amount of milliseconds.

    Example
    -------
    ```python
    from hub import light_matrix
    import runloop

    async def main():
        light_matrix.write("Hi!")
        # Wait for ten seconds
        await runloop.sleep_ms(10000)
        light_matrix.write("Are you still here?")

    runloop.run(main())
    ```

    Parameters
    ----------
    duration : int
        The duration in milliseconds
    """
    pass


async def until(function: Callable[[], bool], timeout: int = 0) -> Awaitable:
    """
    Returns an awaitable that will return when the condition in the function or lambda passed is `True` or when it times out

    Example
    -------
    ```python
    import color_sensor
    import color
    from hub import port
    import runloop

    def is_color_red():
        return color_sensor.color(port.A) is color.RED

    async def main():
        # Wait until Color Sensor sees red
        await runloop.until(is_color_red)
        print("Red!")

    runloop.run(main())
    ```

    Parameters
    ----------
    function : Callable[[], bool]
        A callable with no parameters that returns either `True` or `False`. Callable is anything that can be called, so a `def` or a `lambda`
    timeout : int
        A timeout for the function in milliseconds. If the callable does not return `True` within the timeout, the `until` still resolves after the timeout. 0 means no timeout, in that case it will not resolve until the callable returns `True`
    """
