"""
The light module includes functions to change the color of the light on the SPIKE Prime hub.

To use the Light module add the following import statement to your project:

>>> from hub import light

All functions in the module should be called inside the light module as a prefix like so:

>>> light.color(color.RED)
"""

POWER = 0
"""The power button. On SPIKE Prime it's the button between the left and right buttons."""
CONNECT = 1
"""The light around the Bluetooth connect button on SPIKE Prime."""

def color(light: int, color: int) -> None:
    """
    Change the color of a light on the hub.
    ```python
    from hub import light
    import color

    # Change the light to red
    light.color(light.POWER, color.RED)
    ```

    Parameters
    ----------

    light : int
        The light on the hub
    color : int
        A color from the `color` module
    """
    assert 0 <= color <= 10, "Color must be between 0 and 10"