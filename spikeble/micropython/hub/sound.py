"""
To use the Sound module add the following import statement to your project:

>>> from hub import sound

All functions in the module should be called inside the `sound` module as a prefix like so:

>>> sound.stop()

"""

from typing import Awaitable

ANY = -2
DEFAULT = -1
WAVEFORM_SINE = 1
WAVEFORM_SAWTOOTH = 3
WAVEFORM_SQUARE = 2
WAVEFORM_TRIANGLE = 1

async def beep(freq: int = 440, duration: int = 500, volume: int = 100, *, attack: int = 0, decay: int = 0, sustain: int = 100, release: int = 0, transition: int = 10, waveform: int = WAVEFORM_SINE, channel: int = DEFAULT) -> Awaitable:
    """
    Plays a beep sound from the hub

    Parameters:
        freq: int
            The frequency to play
        duration: int
            The duration in milliseconds
        volume: int
            The volume (0-100)
        attack: int
            The time taken for initial run-up of level from nil to peak, beginning when the key is pressed.
        decay: int
            The time taken for the subsequent run down from the attack level to the designated sustain level.
        sustain: int
            The level during the main sequence of the sound's duration, until the key is released.
        release: int
            The time taken for the level to decay from the sustain level to zero after the key is released
        transition: int
            The time in milliseconds to transition into the sound if something is already playing in the channel
        waveform: int
            The synthesized waveform. Use one of the constants in the `hub.sound` module.
        channel: int
            The desired channel to play on, options are `sound.DEFAULT` and `sound.ANY`
    """
    pass

def stop() -> None:
    """Stops all noise from the hub"""
    pass

def volume(volume: int) -> None:
    """
    Parameters
    ----------
        volume: int
            The volume (0-100)
    """