import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# hub.py
import asyncio
import warnings
from typing import Optional, Type, TypeVar

from bleak import BleakScanner, BleakClient
from bleak.exc import BleakError

from lib.connection import UUID  # SERVICE, RX, TX
from lib.cobs import pack as cobs_pack, unpack as cobs_unpack, DELIMITER
from lib.crc import crc
from lib.messages import (
    BaseMessage, deserialize as msg_deserialize,
    InfoRequest, InfoResponse,
    DeviceNotificationRequest, DeviceNotificationResponse,
    StartFileUploadRequest, StartFileUploadResponse,
    TransferChunkRequest, TransferChunkResponse,
    ProgramFlowRequest, ProgramFlowResponse,
    ClearSlotRequest, ClearSlotResponse,
)

TM = TypeVar("TM", bound=BaseMessage)


class Hub:
    """SPIKE Prime hub over SPIKE App 3 BLE."""

    def __init__(self, *, address: Optional[str] = None, timeout: float = 15.0):
        self.timeout = timeout
        self.address = address
        self.client: Optional[BleakClient] = None

        self._service_uuid = UUID.SERVICE.lower()
        self._rx_uuid: Optional[str] = None
        self._tx_uuid: Optional[str] = None
        self._rx_props: set[str] = set()

        self._notify_started = False
        self._inbuf = bytearray()
        self._queue: "asyncio.Queue[BaseMessage]" = asyncio.Queue()

        self._pending: Optional[tuple[int, asyncio.Future[BaseMessage], type[BaseMessage]]] = None
        self._lock = asyncio.Lock()
        self.info: Optional[InfoResponse] = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.disconnect()

    # ---- connection ----

    async def _pick_device(self):
        if self.address:
            return self.address

        def by_service(dev, adv):
            return any(u.lower() == self._service_uuid for u in (adv.service_uuids or []))

        dev = await BleakScanner.find_device_by_filter(by_service, timeout=self.timeout)
        if dev:
            return dev

        for d in await BleakScanner.discover(timeout=self.timeout):
            det = getattr(d, "details", None)
            uuids = (det.get("uuids") or []) if isinstance(det, dict) else []
            if any(u.lower() == self._service_uuid for u in uuids):
                return d

        raise RuntimeError(f"No SPIKE hub advertising {self._service_uuid}")

    async def connect(self):
        target = await self._pick_device()
        client = BleakClient(target)
        try:
            await client.connect()
        except BleakError as e:
            raise RuntimeError("Bluetooth connect failed") from e
        if not client.is_connected:
            raise RuntimeError("Bluetooth connect failed")

        services = client.services if hasattr(client, "services") else await client.get_services()
        svc = next((s for s in services if s.uuid.lower() == self._service_uuid), None)
        if not svc:
            await client.disconnect()
            raise RuntimeError("SPIKE App 3 service not found")

        # exact UUIDs; fallback by properties if needed
        rx = next((c for c in svc.characteristics if c.uuid.lower() == UUID.RX.lower()), None)
        tx = next((c for c in svc.characteristics if c.uuid.lower() == UUID.TX.lower()), None)
        if not rx or not tx:
            rx = tx = None
            for ch in svc.characteristics:
                p = set(ch.properties or [])
                if not tx and "notify" in p:
                    tx = ch
                if not rx and ("write" in p or "write-without-response" in p):
                    rx = ch
        if not rx or not tx:
            await client.disconnect()
            raise RuntimeError("RX/TX characteristics not found")

        self._rx_uuid, self._tx_uuid = rx.uuid, tx.uuid
        self._rx_props = set(rx.properties or [])
        if ("write" not in self._rx_props) and ("write-without-response" not in self._rx_props):
            await client.disconnect()
            raise RuntimeError("Mapped RX not writable")
        if "notify" not in set(tx.properties or []):
            await client.disconnect()
            raise RuntimeError("Mapped TX not notifiable")

        await client.start_notify(self._tx_uuid, self._on_notify)
        self._notify_started = True
        await asyncio.sleep(0.3)  # allow CCCD to settle on Windows

        self.client = client
        return client

    async def disconnect(self):
        if self.client:
            try:
                if self._notify_started and self._tx_uuid:
                    try:
                        await self.client.stop_notify(self._tx_uuid)
                    except Exception:
                        pass
                if self.client.is_connected:
                    await self.client.disconnect()
            finally:
                self.client = None
                self._notify_started = False
                self._inbuf.clear()
                while not self._queue.empty():
                    try:
                        self._queue.get_nowait()
                        self._queue.task_done()
                    except Exception:
                        break
                if self._pending and not self._pending[1].done():
                    self._pending[1].cancel()
                self._pending = None

    def __del__(self):
        if self.client and getattr(self.client, "is_connected", False):
            warnings.warn("Hub was not properly disconnected.")

    # ---- notify path ----

    def _on_notify(self, _handle: int, data: bytes):
        self._inbuf.extend(data)
        while True:
            try:
                i = self._inbuf.index(DELIMITER)
            except ValueError:
                break
            frame = bytes(self._inbuf[: i + 1])
            del self._inbuf[: i + 1]
            try:
                payload = cobs_unpack(frame)
                msg = msg_deserialize(payload)
            except Exception:
                continue
            self._dispatch(msg)

    def _dispatch(self, msg: BaseMessage):
        if self._pending and self._pending[0] == getattr(msg.__class__, "ID", -1):
            _, fut, _ = self._pending
            if not fut.done():
                fut.set_result(msg)
                return
        self._queue.put_nowait(msg)

    # ---- I/O ----

    async def _write_frame(self, frame: bytes):
        if not self.client or not self.client.is_connected or not self._rx_uuid:
            raise RuntimeError("Not connected")
        if ("write" not in self._rx_props) and ("write-without-response" not in self._rx_props):
            raise RuntimeError("Current RX not writable")
        packet_size = getattr(self.info, "max_packet_size", None) or len(frame)
        use_resp = "write" in self._rx_props
        for off in range(0, len(frame), packet_size):
            chunk = frame[off:off + packet_size]
            await self.client.write_gatt_char(self._rx_uuid, chunk, response=use_resp)

    async def send_message(self, message: BaseMessage) -> None:
        await self._write_frame(cobs_pack(message.serialize()))

    async def send_request(self, message: BaseMessage, response_type: Type[TM], timeout: float = 5.0) -> TM:
        async with self._lock:
            if self._pending and not self._pending[1].done():
                raise RuntimeError("Another request is pending")
            fut: asyncio.Future[BaseMessage] = asyncio.get_event_loop().create_future()
            exp_id = getattr(response_type, "ID", None)
            if exp_id is None:
                raise RuntimeError("response_type must define ID")
            self._pending = (exp_id, fut, response_type)
            try:
                await self.send_message(message)
                res = await asyncio.wait_for(fut, timeout=timeout)
                return res  # type: ignore[return-value]
            finally:
                self._pending = None

    async def recv(self, timeout: Optional[float] = None) -> BaseMessage:
        if timeout is None:
            return await self._queue.get()
        return await asyncio.wait_for(self._queue.get(), timeout=timeout)

    # ---- high-level ops ----

    async def get_info(self) -> InfoResponse:
        self.info = await self.send_request(InfoRequest(), InfoResponse, timeout=5.0)
        return self.info

    async def enable_notifications(self, period_ms: int = 50) -> DeviceNotificationResponse:
        return await self.send_request(DeviceNotificationRequest(period_ms), DeviceNotificationResponse, timeout=5.0)

    async def clear_slot(self, slot: int) -> ClearSlotResponse:
        return await self.send_request(ClearSlotRequest(slot), ClearSlotResponse, timeout=5.0)

    async def start_program(self, slot: int) -> ProgramFlowResponse:
        return await self.send_request(ProgramFlowRequest(False, slot), ProgramFlowResponse, timeout=5.0)

    async def stop_program(self, slot: int) -> ProgramFlowResponse:
        return await self.send_request(ProgramFlowRequest(True, slot), ProgramFlowResponse, timeout=5.0)

    async def upload_program(self, *, slot: int, name: str, data: bytes) -> None:
        if not self.info:
            await self.get_info()
        max_chunk = self.info.max_chunk_size
        total_crc = crc(data, 0)
        _ = await self.send_request(
            StartFileUploadRequest(name, slot, total_crc),
            StartFileUploadResponse,
            timeout=10.0,
        )
        running = 0
        for off in range(0, len(data), max_chunk):
            chunk = data[off:off + max_chunk]
            running = crc(chunk, running)
            _ = await self.send_request(
                TransferChunkRequest(running, chunk),
                TransferChunkResponse,
                timeout=10.0,
            )
        _ = await self.start_program(slot)


# minimal demo
if __name__ == "__main__":
    async def main():
        # set address explicitly for reliability on Windows
        from lib.connection import Hardware
        async with Hub(address=getattr(Hardware, "MAC_ADDR", None)) as hub:
            try:
                info = await hub.get_info()
                print(f"Info rpc={info.rpc_major}.{info.rpc_minor} "
                      f"max_packet={info.max_packet_size} max_chunk={info.max_chunk_size}")
            except asyncio.TimeoutError:
                print("InfoRequest timed out")

            try:
                _ = await hub.enable_notifications(50)
            except asyncio.TimeoutError:
                print("Enable notifications timed out")

            for _ in range(5):
                try:
                    m = await hub.recv(timeout=3)
                    print(m)
                except asyncio.TimeoutError:
                    print("timeout")

    asyncio.run(main())