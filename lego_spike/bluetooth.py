import asyncio
from bleak import BleakScanner, BleakClient
from bleak.exc import BleakDBusError
import warnings

try:
    from .lib import UUID, pack, unpack, DELIMITER
except ImportError:
    from lib import UUID, pack, unpack, DELIMITER


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
            # Try to get uuids from metadata (Bleak >=0.20), else from details (older Bleak), else empty list
            uuids = []
            if hasattr(device, "metadata") and device.metadata:
                uuids = device.metadata.get("uuids") or []
            elif hasattr(device, "details") and isinstance(device.details, dict):
                uuids = device.details.get("uuids") or []
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
    
    async def start(self):
        """Begin TX notifications and deframing loop."""
        if not self.client or not self.client.is_connected:
            raise RuntimeError("Not connected")
        if self._notify_started:
            return
        await self.client.start_notify(UUID.TX, self._on_notify)
        self._notify_started = True
    
    async def send(self, payload: bytes):
        """COBS-pack and write one SPIKE App 3 frame to RX."""
        if not self.client or not self.client.is_connected:
            raise RuntimeError("Not connected")
        frame = pack(payload)
        await self.client.write_gatt_char(UUID.RX, frame, response=False)

    async def recv(self, timeout: float | None = None) -> bytes:
        """Await one deframed payload from notifications."""
        if timeout is None:
            return await self._queue.get()
        return await asyncio.wait_for(self._queue.get(), timeout=timeout)
    
    def _on_notify(self, _handle: int, data: bytes):
        """Accumulate bytes, split on 0x02 delimiter, unpack each frame."""
        self._inbuf.extend(data)
        while True:
            try:
                idx = self._inbuf.index(DELIMITER)
            except ValueError:
                break  # no full frame yet
            frame = bytes(self._inbuf[: idx + 1])
            del self._inbuf[: idx + 1]
            try:
                payload = unpack(frame)
            except Exception:
                # Corrupt frame; drop buffer in worst case to resync
                continue
            # Push decoded payload to consumer
            self._queue.put_nowait(payload)

    async def disconnect(self):
        if self.client:
            try:
                if self._notify_started:
                    try:
                        await self.client.stop_notify(UUID.TX)
                    except Exception:
                        pass
                if self.client.is_connected:
                    await self.client.disconnect()
            finally:
                self.client = None
                self._notify_started = False
                self._inbuf.clear()
                # drain queue without awaiting
                while not self._queue.empty():
                    try:
                        self._queue.get_nowait()
                        self._queue.task_done()
                    except Exception:
                        break

    def __del__(self):
        # Warn: __del__ can't await, so just a placeholder for cleanup
        if self.client and self.client.is_connected:
            # In production, consider using context managers instead
            warnings.warn("Bluetooth client was not properly disconnected.")


if __name__ == "__main__":

    async def main():
        async with Bluetooth() as bt:
            await bt.start()

            # 1) InfoRequest (0x00)
            await bt.send(b"\x00")
            try:
                msg = await bt.recv(timeout=2.0)
                if msg and msg[0] == 0x01:
                    # Minimal parse example: print protocol version and max packet sizes
                    rpc_major = msg[1]
                    rpc_minor = msg[2]
                    max_packet = int.from_bytes(msg[7:9], "little")
                    max_chunk = int.from_bytes(msg[11:13], "little")
                    print(
                        f"InfoResponse rpc={rpc_major}.{rpc_minor} "
                        f"max_packet={max_packet} max_chunk={max_chunk}"
                    )
                else:
                    print("Unexpected first message:", msg.hex() if msg else None)
            except asyncio.TimeoutError:
                print("No InfoResponse")

            # 2) DeviceNotificationRequest (0x28) every 50 ms
            period_ms = 50
            await bt.send(bytes([0x28]) + period_ms.to_bytes(2, "little"))

            # 3) Read a few notifications
            for _ in range(5):
                try:
                    msg = await bt.recv(timeout=3.0)
                    print("RX:", msg.hex())
                except asyncio.TimeoutError:
                    print("No notification within timeout")

    asyncio.run(main())
