import sys

sys.path.append("..")

import spikeble
import asyncio


def main():
    # from app import sound, bargraph, display, linegraph, music
    import color
    import color_matrix
    import color_sensor
    import device
    import distance_sensor
    import force_sensor
    import hub
    from hub import port, button, light, light_matrix, motion_sensor, sound
    import motor
    import motor_pair
    import orientation
    import runloop


    ### Insert Your Code Here ###


if __name__ == "__main__":
    asyncio.run(spikeble.run(main))
