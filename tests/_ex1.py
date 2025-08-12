import runloop
import motor_pair
from hub import port, light_matrix
from hub import sound as hub_sound
# === Robot configuration ===
LEFT_MOTOR_PORT = port.B
RIGHT_MOTOR_PORT = port.E
PAIR = motor_pair.PAIR_1
DEFAULT_VELOCITY = 720  # deg/s
WHEEL_CIRCUMFERENCE_CM = 17.5  # SPIKE Prime wheel

async def move_cm(cm):
    degrees = int((cm / WHEEL_CIRCUMFERENCE_CM) * 360)
    await motor_pair.move_for_degrees(PAIR, degrees, 0, velocity=DEFAULT_VELOCITY)

async def playsong():
    await hub_sound.beep(400, 1000, 100)
    await hub_sound.beep(450, 500, 100)
    await hub_sound.beep(500, 1000, 100)

async def main():
    motor_pair.pair(PAIR, LEFT_MOTOR_PORT, RIGHT_MOTOR_PORT)
    await playsong()
    await move_cm(20)

runloop.run(main())