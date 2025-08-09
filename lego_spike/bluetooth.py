import asyncio
from bleak import BleakScanner, BleakClient
from bleak.exc import BleakDBusError

try:
    from .lib.connection import UUID
except ImportError:
    from lib.connection import UUID
import warnings


class Bluetooth:
    """
    Manages Bluetooth connections using Bleak.
    """

    def __init__(self, timeout=10):
        self.timeout = timeout
        self.client = None
        self.target_uuid = UUID.SERVICE.lower()

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.disconnect()

    async def connect(self):
        """
        Connect to a Bluetooth device advertising the given UUID.
        Returns the BleakClient if successful, else raises an exception.
        """
        try:
            devices = await BleakScanner.discover(timeout=self.timeout)
        except BleakDBusError as e:
            raise RuntimeError(
                "Bluetooth is not enabled or the Bluetooth service is not running."
            ) from e

        for device in devices:
            uuids = device.metadata.get("uuids") or []
            if any(u.lower() == self.target_uuid for u in uuids):
                client = BleakClient(device)
                try:
                    await client.connect()
                    if client.is_connected:
                        self.client = client
                        return client
                except Exception:
                    await client.disconnect()
                break
        raise RuntimeError(f"No device found advertising UUID {self.target_uuid}")

    async def disconnect(self):
        """
        Disconnects the current BleakClient if connected.
        """
        if self.client:
            if self.client.is_connected:
                await self.client.disconnect()
            self.client = None

    def __del__(self):
        # Warn: __del__ can't await, so just a placeholder for cleanup
        if self.client and self.client.is_connected:
            # In production, consider using context managers instead
            warnings.warn("Bluetooth client was not properly disconnected.")


if __name__ == "__main__":

    async def main():
        async with Bluetooth() as bt:
            print(f"Connected: {bt.client.is_connected}")

    asyncio.run(main())
