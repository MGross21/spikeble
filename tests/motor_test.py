# test_control.py - Fixed test suite for LEGO SPIKE Prime
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
from spike.hub.hub import Hub
from spike.hub.motor import (
    # Motor functions
    motor_run_degrees, motor_start_stop, motor_to_position, motor_get_position,
    motor_reset_position, motor_run_time,
    
    # Motor pair functions  
    motor_pair_move, motor_pair_move_distance, motor_pair_turn, motor_pair_stop,
    
    # Sensor functions
    color_sensor_read, distance_sensor_read, force_sensor_read,
    
    # Hub display and interaction
    hub_display_image, hub_display_text, hub_play_sound, hub_play_beep,
    hub_set_status_light, hub_read_buttons, hub_get_orientation,
    
    # Utility functions
    emergency_stop_all, system_info, wait_for_button_press, simple_test
)
from lib.enumeration import HubPort


async def test_simple():
    """Run the simple connectivity and functionality test."""
    async with Hub() as hub:
        print("=== Simple SPIKE Prime Test ===")
        
        # Get hub info
        info = await hub.get_info()
        print(f"Connected to hub: RPC {info.rpc_major}.{info.rpc_minor}")
        
        # Run the comprehensive simple test
        await simple_test(hub, slot=0)
        

async def test_individual_motors():
    """Test individual motor operations."""
    async with Hub() as hub:
        print("=== Testing Individual Motors ===")
        
        print("\n1. Testing motor A - 180 degrees at speed 25...")
        await motor_run_degrees(hub, port=HubPort.A, degrees=180, speed=25)
        
        print("\n2. Getting motor A position...")
        await motor_get_position(hub, port=HubPort.A)
        
        print("\n3. Testing motor B - start/stop for 2 seconds...")
        await motor_start_stop(hub, port='B', speed=30, seconds=2.0)
        
        print("\n4. Testing motor C - move to position 45...")
        await motor_to_position(hub, port='C', position=45, speed=20)
        
        print("\n5. Testing motor D - run for 1 second (1000ms)...")
        await motor_run_time(hub, port=HubPort.D, speed=40, time_ms=1000)


async def test_hub_features():
    """Test hub display, sound, and interaction features."""
    async with Hub() as hub:
        print("=== Testing Hub Features ===")
        
        print("\n1. Displaying HAPPY image...")
        await hub_display_image(hub, image="HAPPY")
        
        print("\n2. Setting status light to green...")
        await hub_set_status_light(hub, color="green")
        
        print("\n3. Playing Hello sound...")
        await hub_play_sound(hub, sound="Hello")
        
        print("\n4. Playing beep...")
        await hub_play_beep(hub, note=60, seconds=0.5)
        
        print("\n5. Displaying scrolling text...")
        await hub_display_text(hub, text="SPIKE")
        
        print("\n6. Getting system information...")
        await system_info(hub)
        
        print("\n7. Getting hub orientation...")
        await hub_get_orientation(hub)


async def test_sensors():
    """Test sensor reading functions."""
    async with Hub() as hub:
        print("=== Testing Sensors ===")
        
        print("\n1. Attempting color sensor on port A...")
        await color_sensor_read(hub, port=HubPort.A)
        
        print("\n2. Attempting distance sensor on port B...")
        await distance_sensor_read(hub, port=HubPort.B)
        
        print("\n3. Attempting force sensor on port C...")
        await force_sensor_read(hub, port=HubPort.C)


async def test_motor_pairs():
    """Test motor pair operations."""
    async with Hub() as hub:
        print("=== Testing Motor Pairs ===")
        
        print("\n1. Starting motor pair (E,F) forward...")
        await motor_pair_move(hub, left_port=HubPort.E, right_port=HubPort.F, steering=0, speed=30)
        
        await asyncio.sleep(2)
        
        print("\n2. Stopping motor pair...")
        await motor_pair_stop(hub, left_port=HubPort.E, right_port=HubPort.F)
        
        print("\n3. Moving 5cm forward...")
        await motor_pair_move_distance(hub, left_port=HubPort.E, right_port=HubPort.F, 
                                      distance_cm=5, steering=0, speed=25)
        
        print("\n4. Turning 45 degrees right...")
        await motor_pair_turn(hub, left_port=HubPort.E, right_port=HubPort.F, degrees=45, speed=25)


async def test_debug_connection():
    """Debug the connection and message handling."""
    async with Hub() as hub:
        print("=== Debug Connection Test ===")
        
        info = await hub.get_info()
        print(f"Hub info: RPC {info.rpc_major}.{info.rpc_minor}")
        print(f"Max packet size: {info.max_packet_size}")
        print(f"Max chunk size: {info.max_chunk_size}")
        
        # Enable notifications to see what we're getting
        await hub.enable_notifications(50)
        
        # Send a very simple program and monitor output
        simple_code = """
print("Hello from SPIKE Prime!")
print("This is a test message")
from spike import PrimeHub
hub = PrimeHub()
hub.light_matrix.show_image('HAPPY')
print("Program completed successfully")
"""
        print("\nRunning simple debug program...")
        await hub.run_source(slot=0, name="debug.py", source=simple_code, follow_seconds=3.0)


async def quick_test():
    """Quick functionality test."""
    async with Hub() as hub:
        info = await hub.get_info()
        print(f"Connected! RPC version: {info.rpc_major}.{info.rpc_minor}")
        
        # Very simple test
        code = """
print("=== SPIKE Prime Quick Test ===")
from spike import PrimeHub
hub = PrimeHub()
hub.light_matrix.show_image('HEART')
print("Heart displayed on LED matrix")
hub.status_light.on('cyan')
print("Status light set to cyan")
print("Quick test completed!")
"""
        await hub.run_source(slot=0, name="quick.py", source=code, follow_seconds=2.0)


async def comprehensive_test():
    """Run comprehensive tests."""
    print("Starting comprehensive LEGO SPIKE Prime tests...")
    print("Make sure you have motors connected for full testing!")
    
    try:
        print("\n" + "="*50)
        print("SIMPLE TEST")
        print("="*50)
        await test_simple()
        
        print("\n" + "="*50)
        print("HUB FEATURES TEST")
        print("="*50)
        await test_hub_features()
        
        print("\n" + "="*50)
        print("INDIVIDUAL MOTOR TEST")
        print("="*50)
        await test_individual_motors()
        
        print("\n" + "="*50)
        print("SENSOR TEST")
        print("="*50)
        await test_sensors()
        
        print("\n" + "="*50)
        print("MOTOR PAIR TEST")
        print("="*50)
        await test_motor_pairs()
        
        print("\n" + "="*50)
        print("ALL TESTS COMPLETED!")
        print("="*50)
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test LEGO SPIKE Prime control functions")
    parser.add_argument("--quick", action="store_true", help="Run quick test only")
    parser.add_argument("--simple", action="store_true", help="Run simple test only")  
    parser.add_argument("--debug", action="store_true", help="Run debug connection test")
    parser.add_argument("--motors", action="store_true", help="Test individual motors only")
    parser.add_argument("--motor-pairs", action="store_true", help="Test motor pairs only")
    parser.add_argument("--sensors", action="store_true", help="Test sensors only")
    parser.add_argument("--hub", action="store_true", help="Test hub features only")
    
    args = parser.parse_args()
    
    if args.quick:
        asyncio.run(quick_test())
    elif args.simple:
        asyncio.run(test_simple())
    elif args.debug:
        asyncio.run(test_debug_connection())
    elif args.motors:
        asyncio.run(test_individual_motors())
    elif args.motor_pairs:
        asyncio.run(test_motor_pairs())
    elif args.sensors:
        asyncio.run(test_sensors())
    elif args.hub:
        asyncio.run(test_hub_features())
    else:
        asyncio.run(comprehensive_test())