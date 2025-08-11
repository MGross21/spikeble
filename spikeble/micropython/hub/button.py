"""
This module allows you to react to buttons being pressed on the hub. You must first import the `button` module to use the buttons.

To use the Button module add the following import statement to your project:


>>> from hub import button

All functions in the module should be called inside the `button` module as a prefix like so:

>>> button.pressed(button.LEFT)

"""

LEFT = 1
"""Left button next to the power button on the SPIKE Prime hub"""
RIGHT = 2
"""Right button next to the power button on the SPIKE Prime hub"""

def pressed(button: int) -> int:
    """
    ```python
    from hub import button
    left_button_press_duration = 0

    # Wait for the left button to be pressed
    while not button.pressed(button.LEFT):
        pass
    
    # As long as the left button is being pressed, update the `left_button_press_duration` variable
    while button.pressed(button.LEFT):
        left_button_press_duration = button.pressed(button.LEFT)
    
    print("Left button was pressed for " + str(left_button_press_duration) + " milliseconds")
    ```
    """
