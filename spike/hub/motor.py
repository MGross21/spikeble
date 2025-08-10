from ..lib.enumeration import HubPort
from .hub import Hub


def _port_name(p):  # accept enum or 'A'..'F'
    """Convert port to string name."""
    if isinstance(p, HubPort):
        return p.name
    raise ValueError(f"Invalid port: {p}")


async def motor_run_degrees(hub: Hub, *, port: HubPort | str, degrees: int, speed: int, slot: int = 1):
    """Run motor for specified degrees at given speed."""
    code = f"""
from spike import Motor
motor = Motor('{_port_name(port)}')
motor.run_for_degrees({degrees}, {speed})
print("Motor {_port_name(port)} ran {degrees} degrees at speed {speed}")
"""
    await hub.run_source(slot=slot, name="motor.py", source=code, follow_seconds=3.0)


async def motor_start_stop(hub: Hub, *, port: HubPort | str, speed: int, seconds: float, slot: int = 1):
    """Start motor, run for specified time, then stop."""
    code = f"""
from spike import Motor
import utime
motor = Motor('{_port_name(port)}')
motor.start({speed})
print("Motor {_port_name(port)} started at speed {speed}")
utime.sleep({seconds})
motor.stop()
print("Motor {_port_name(port)} stopped after {seconds} seconds")
"""
    await hub.run_source(slot=slot, name="motor_run.py", source=code, follow_seconds=seconds + 2.0)


async def motor_to_position(hub: Hub, *, port: HubPort | str, position: int, speed: int, slot: int = 1):
    """Move motor to absolute position at given speed."""
    code = f"""
from spike import Motor
motor = Motor('{_port_name(port)}')
motor.run_to_position({position}, {speed})
print("Motor {_port_name(port)} moved to position {position}")
"""
    await hub.run_source(slot=slot, name="motor_pos.py", source=code, follow_seconds=3.0)


async def motor_get_position(hub: Hub, *, port: HubPort | str, slot: int = 1, follow_seconds: float = 2.0):
    """Get current motor position."""
    code = f"""
from spike import Motor
motor = Motor('{_port_name(port)}')
position = motor.get_position()
print("Motor {_port_name(port)} position:", position)
"""
    await hub.run_source(slot=slot, name="motor_pos_read.py", source=code, follow_seconds=follow_seconds)


async def motor_reset_position(hub: Hub, *, port: HubPort | str, position: int = 0, slot: int = 1):
    """Reset motor position to specified value (default 0)."""
    code = f"""
from spike import Motor
motor = Motor('{_port_name(port)}')
motor.set_position({position})
print("Motor {_port_name(port)} position reset to {position}")
"""
    await hub.run_source(slot=slot, name="motor_reset.py", source=code, follow_seconds=1.0)


async def motor_run_time(hub: Hub, *, port: HubPort | str, speed: int, time_ms: int, slot: int = 1):
    """Run motor for specified time in milliseconds."""
    code = f"""
from spike import Motor
motor = Motor('{_port_name(port)}')
motor.run_for_time({time_ms}, {speed})
print("Motor {_port_name(port)} ran for {time_ms}ms at speed {speed}")
"""
    await hub.run_source(slot=slot, name="motor_time.py", source=code, follow_seconds=time_ms/1000.0 + 2.0)


async def color_sensor_read(hub: Hub, *, port: HubPort | str, slot: int = 1, follow_seconds: float = 2.0):
    """Read color sensor values."""
    code = f"""
from spike import ColorSensor
sensor = ColorSensor('{_port_name(port)}')
try:
    color = sensor.get_color()
    reflected = sensor.get_reflected_light()
    ambient = sensor.get_ambient_light()
    print("Color sensor on port {_port_name(port)}:")
    print("  Color:", color)
    print("  Reflected light:", reflected, "%")
    print("  Ambient light:", ambient, "%")
except Exception as e:
    print("Error reading color sensor:", str(e))
"""
    await hub.run_source(slot=slot, name="color_sensor.py", source=code, follow_seconds=follow_seconds)


async def distance_sensor_read(hub: Hub, *, port: HubPort | str, slot: int = 1, follow_seconds: float = 2.0):
    """Read ultrasonic distance sensor."""
    code = f"""
from spike import DistanceSensor
sensor = DistanceSensor('{_port_name(port)}')
try:
    distance = sensor.get_distance_cm()
    print("Distance sensor on port {_port_name(port)}:")
    if distance is None:
        print("  Distance: Out of range")
    else:
        print("  Distance:", distance, "cm")
except Exception as e:
    print("Error reading distance sensor:", str(e))
"""
    await hub.run_source(slot=slot, name="distance_sensor.py", source=code, follow_seconds=follow_seconds)


async def force_sensor_read(hub: Hub, *, port: HubPort | str, slot: int = 1, follow_seconds: float = 2.0):
    """Read force sensor values."""
    code = f"""
from spike import ForceSensor
sensor = ForceSensor('{_port_name(port)}')
try:
    force_n = sensor.get_force_newton()
    force_pct = sensor.get_force_percentage()
    pressed = sensor.is_pressed()
    print("Force sensor on port {_port_name(port)}:")
    print("  Force (N):", force_n)
    print("  Force (%):", force_pct)
    print("  Is pressed:", pressed)
except Exception as e:
    print("Error reading force sensor:", str(e))
"""
    await hub.run_source(slot=slot, name="force_sensor.py", source=code, follow_seconds=follow_seconds)


async def hub_display_image(hub: Hub, *, image: str = "HAPPY", slot: int = 1):
    """Display an image on the hub's LED matrix."""
    code = f"""
from spike import PrimeHub
hub = PrimeHub()
hub.light_matrix.show_image('{image}')
print("Displayed image: {image}")
"""
    await hub.run_source(slot=slot, name="display.py", source=code, follow_seconds=1.0)


async def hub_display_text(hub: Hub, *, text: str, slot: int = 1):
    """Display scrolling text on the hub's LED matrix."""
    code = f"""
from spike import PrimeHub
hub = PrimeHub()
hub.light_matrix.write('{text}')
print("Displayed text: {text}")
"""
    await hub.run_source(slot=slot, name="display_text.py", source=code, follow_seconds=3.0)


async def hub_play_sound(hub: Hub, *, sound: str = "Hello", slot: int = 1):
    """Play a sound on the hub speaker."""
    code = f"""
from spike import PrimeHub
hub = PrimeHub()
hub.speaker.play_sound('{sound}')
print("Played sound: {sound}")
"""
    await hub.run_source(slot=slot, name="play_sound.py", source=code, follow_seconds=2.0)


async def hub_play_beep(hub: Hub, *, note: int = 60, seconds: float = 1.0, slot: int = 1):
    """Play a beep tone. Note: 60 = Middle C, range usually 44-123."""
    code = f"""
from spike import PrimeHub
hub = PrimeHub()
hub.speaker.beep({note}, {seconds})
print("Played beep: note {note} for {seconds} seconds")
"""
    await hub.run_source(slot=slot, name="beep.py", source=code, follow_seconds=seconds + 1.0)


async def hub_set_status_light(hub: Hub, *, color: str = "azure", slot: int = 1):
    """Set the hub's status light color."""
    code = f"""
from spike import PrimeHub
hub = PrimeHub()
hub.status_light.on('{color}')
print("Status light set to: {color}")
"""
    await hub.run_source(slot=slot, name="status_light.py", source=code, follow_seconds=1.0)


async def hub_read_buttons(hub: Hub, *, slot: int = 1, follow_seconds: float = 5.0):
    """Read hub button states."""
    code = f"""
from spike import PrimeHub
import utime
hub = PrimeHub()
print("Press buttons on the hub (monitoring for {follow_seconds} seconds)...")
end_time = utime.time() + {follow_seconds}
while utime.time() < end_time:
    left = hub.left_button.is_pressed()
    right = hub.right_button.is_pressed()
    bluetooth = hub.bluetooth_button.is_pressed()
    if left or right or bluetooth:
        print(f"Buttons - Left: {{left}}, Right: {{right}}, Bluetooth: {{bluetooth}}")
    utime.sleep(0.5)
print("Button monitoring finished")
"""
    await hub.run_source(slot=slot, name="buttons.py", source=code, follow_seconds=follow_seconds + 1.0)


async def hub_get_orientation(hub: Hub, *, slot: int = 1, follow_seconds: float = 2.0):
    """Get hub orientation and motion sensor data."""
    code = """
from spike import PrimeHub
hub = PrimeHub()
try:
    orientation = hub.motion_sensor.get_orientation()
    yaw = hub.motion_sensor.get_yaw_angle()
    pitch = hub.motion_sensor.get_pitch_angle() 
    roll = hub.motion_sensor.get_roll_angle()
    print("Hub orientation and motion:")
    print("  Orientation:", orientation)
    print("  Yaw angle:", yaw)
    print("  Pitch angle:", pitch)
    print("  Roll angle:", roll)
except Exception as e:
    print("Error reading motion sensor:", str(e))
"""
    await hub.run_source(slot=slot, name="orientation.py", source=code, follow_seconds=follow_seconds)


async def motor_pair_move(hub: Hub, *, left_port: HubPort | str, right_port: HubPort | str, 
                         steering: int = 0, speed: int = 50, slot: int = 1):
    """Move a motor pair (like drive base). Steering: -100 (left) to 100 (right)."""
    code = f"""
from spike import MotorPair
pair = MotorPair('{_port_name(left_port)}', '{_port_name(right_port)}')
pair.start({steering}, {speed})
print("Motor pair started - steering: {steering}, speed: {speed}")
"""
    await hub.run_source(slot=slot, name="motor_pair.py", source=code, follow_seconds=1.0)


async def motor_pair_move_distance(hub: Hub, *, left_port: HubPort | str, right_port: HubPort | str,
                                  distance_cm: int, steering: int = 0, speed: int = 50, slot: int = 1):
    """Move a motor pair for a specific distance in cm."""
    direction = "forward" if distance_cm >= 0 else "backward"
    code = f"""
from spike import MotorPair
pair = MotorPair('{_port_name(left_port)}', '{_port_name(right_port)}')
pair.move({abs(distance_cm)}, '{direction}', {steering}, {speed})
print("Motor pair moved {distance_cm}cm {direction}")
"""
    await hub.run_source(slot=slot, name="motor_pair_distance.py", source=code, follow_seconds=5.0)


async def motor_pair_turn(hub: Hub, *, left_port: HubPort | str, right_port: HubPort | str,
                         degrees: int, speed: int = 50, slot: int = 1):
    """Turn a motor pair by specified degrees."""
    direction = "right" if degrees > 0 else "left"
    code = f"""
from spike import MotorPair
pair = MotorPair('{_port_name(left_port)}', '{_port_name(right_port)}')
pair.move({abs(degrees)}, '{direction}', 100, {speed})
print("Motor pair turned {degrees} degrees {direction}")
"""
    await hub.run_source(slot=slot, name="motor_pair_turn.py", source=code, follow_seconds=3.0)


async def motor_pair_stop(hub: Hub, *, left_port: HubPort | str, right_port: HubPort | str, slot: int = 1):
    """Stop a motor pair."""
    code = f"""
from spike import MotorPair
pair = MotorPair('{_port_name(left_port)}', '{_port_name(right_port)}')
pair.stop()
print("Motor pair stopped")
"""
    await hub.run_source(slot=slot, name="motor_pair_stop.py", source=code, follow_seconds=1.0)


# Utility functions for common operations
async def emergency_stop_all(hub: Hub, *, slot: int = 1):
    """Stop all motors immediately."""
    code = """
from spike import Motor
ports = ['A', 'B', 'C', 'D', 'E', 'F']
stopped_count = 0
for port in ports:
    try:
        motor = Motor(port)
        motor.stop()
        print(f"Stopped motor on port {port}")
        stopped_count += 1
    except Exception as e:
        pass  # Port may not have a motor
print(f"Emergency stop completed - stopped {stopped_count} motors")
"""
    await hub.run_source(slot=slot, name="emergency_stop.py", source=code, follow_seconds=2.0)


async def system_info(hub: Hub, *, slot: int = 1, follow_seconds: float = 3.0):
    """Get system information from the hub."""
    code = """
from spike import PrimeHub
import gc
hub = PrimeHub()
try:
    voltage = hub.battery.voltage()
    current = hub.battery.current()
    capacity = hub.battery.capacity_left()
    print("System Information:")
    print("  Battery voltage:", voltage, "V")
    print("  Battery current:", current, "A") 
    print("  Battery capacity:", capacity, "%")
    print("  Free memory:", gc.mem_free(), "bytes")
    print("  Allocated memory:", gc.mem_alloc(), "bytes")
except Exception as e:
    print("Error reading system info:", str(e))
"""
    await hub.run_source(slot=slot, name="system_info.py", source=code, follow_seconds=follow_seconds)


async def wait_for_button_press(hub: Hub, *, button: str = "left", slot: int = 1, follow_seconds: float = 10.0):
    """Wait for a specific button press. Button: 'left', 'right', or 'bluetooth'."""
    code = f"""
from spike import PrimeHub
import utime
hub = PrimeHub()
print("Waiting for {button} button press...")
start_time = utime.time()
while utime.time() - start_time < {follow_seconds}:
    if hub.{button}_button.is_pressed():
        print("{button.capitalize()} button pressed!")
        break
    utime.sleep(0.1)
else:
    print("Timeout - no button press detected")
"""
    await hub.run_source(slot=slot, name="wait_button.py", source=code, follow_seconds=follow_seconds)


async def simple_test(hub: Hub, *, slot: int = 1):
    """Simple test to verify the connection and basic functionality."""
    code = """
from spike import PrimeHub, Motor
import utime

print("=== SPIKE Prime Simple Test ===")

# Test hub
hub = PrimeHub()
print("Hub connected successfully!")

# Test display
hub.light_matrix.show_image('HAPPY')
print("Display: Showing HAPPY face")

# Test status light
hub.status_light.on('blue')
print("Status light: Blue")

# Test speaker
hub.speaker.beep(60, 0.5)
print("Speaker: Played beep")

# Test motor (if connected to port A)
try:
    motor = Motor('A')
    print("Motor A: Connected")
    motor.run_for_degrees(90, 25)
    print("Motor A: Ran 90 degrees")
    position = motor.get_position()
    print("Motor A: Position =", position)
except Exception as e:
    print("Motor A: Not connected or error:", str(e))

print("=== Test Complete ===")
"""
    await hub.run_source(slot=slot, name="simple_test.py", source=code, follow_seconds=5.0)