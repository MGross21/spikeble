import runloop
import motor_pair
from hub import port, light_matrix
from hub import sound as hub_sound

# === Robot configuration (edit to match your build) ===
LEFT_MOTOR_PORT = port.B
RIGHT_MOTOR_PORT = port.E
PAIR = motor_pair.PAIR_1
DEFAULT_VELOCITY = 720   # deg/s (typical range ~200..1000)
WHEEL_CIRCUMFERENCE_CM = 17.5  # SPIKE Prime wheel ~17.5 cm

def set_velocity_from_power(p):
    """Map 0..100 power to deg/s (~0..1000). If a raw deg/s is passed, use it directly."""
    global DEFAULT_VELOCITY
    try:
        p = int(p)
    except Exception:
        p = 50
    if 0 <= p <= 100:
        DEFAULT_VELOCITY = max(1, p * 10)
    else:
        DEFAULT_VELOCITY = max(1, p)

def start_moving_straight():
    motor_pair.move(PAIR, 0, velocity=DEFAULT_VELOCITY)

def stop_moving():
    motor_pair.stop(PAIR)

async def move_degrees(deg):
    await motor_pair.move_for_degrees(PAIR, int(deg), 0, velocity=DEFAULT_VELOCITY)

async def move_cm(cm):
    deg = int((cm / WHEEL_CIRCUMFERENCE_CM) * 360)
    await motor_pair.move_for_degrees(PAIR, deg, 0, velocity=DEFAULT_VELOCITY)

async def turn_left_deg(deg):
    await motor_pair.move_tank_for_degrees(PAIR, int(deg), -DEFAULT_VELOCITY, DEFAULT_VELOCITY)

async def turn_right_deg(deg):
    await motor_pair.move_tank_for_degrees(PAIR, int(deg), DEFAULT_VELOCITY, -DEFAULT_VELOCITY)

async def playsong():
    await hub_sound.beep(400, 1000, 100)
    await hub_sound.beep(450, 500, 100)
    await hub_sound.beep(500, 1000, 100)

async def main():
    motor_pair.pair(PAIR, LEFT_MOTOR_PORT, RIGHT_MOTOR_PORT)

    # Start mission
    await playsong()
    await move_cm(20)

runloop.run(main())