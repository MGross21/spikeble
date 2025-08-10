# bt_spike_connect.py
import asyncio
from bleak import BleakClient

SERVICE = "0000fd02-0000-1000-8000-00805f9b34fb"
RX = "0000fd02-0001-1000-8000-00805f9b34fb"
TX = "0000fd02-0002-1000-8000-00805f9b34fb"
ADDR = "3C:E4:B0:AB:D3:3A"  # your hub

async def main():
    async with BleakClient(ADDR) as client:
        if not client.is_connected:
            raise RuntimeError("Failed to connect")
        print("Connected to hub:", ADDR)

        # get services (handles both new and old Bleak)
        services = client.services if hasattr(client, "services") else await client.get_services()
        print("Services:")
        for svc in services:
            print(f"  {svc.uuid}")
            for ch in svc.characteristics:
                print(f"    Char: {ch.uuid} props={ch.properties}")

        # verify SPIKE App 3 chars exist
        have = {c.uuid.lower() for s in services for c in s.characteristics}
        assert RX in have and TX in have, "SPIKE RX/TX not found"

if __name__ == "__main__":
    asyncio.run(main())
