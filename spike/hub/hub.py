# hub.py
import os
import asyncio
import warnings
from typing import Optional, Type, TypeVar

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bleak import BleakScanner, BleakClient
from bleak.exc import BleakError

# project modules
from lib.connection import UUID, Hardware  # service/char UUIDs, default MAC
from lib.cobs import pack as cobs_pack, unpack as cobs_unpack, DELIMITER
from lib.crc import crc
from lib.messages import (
    BaseMessage,
    deserialize as msg_deserialize,
    InfoRequest, InfoResponse,
    DeviceNotificationRequest, DeviceNotificationResponse,
    StartFileUploadRequest, StartFileUploadResponse,
    TransferChunkRequest, TransferChunkResponse,
    ProgramFlowRequest, ProgramFlowResponse,
    ClearSlotRequest, ClearSlotResponse,
)

TM = TypeVar("TM", bound=BaseMessage)


class Hub:
    """
    SPIKE Prime hub.
    - connect()/disconnect()
    - send_message()/send_request()
    - get_info(), enable_notifications()
    - clear_slot(), start_program(), stop_program()
    - upload_program()
    """

    def __init__(self, *, address: Optional[str] = None, timeout: float = 15.0):
        self.timeout = timeout
        self.address = address or Hardware.MAC_ADDR
        self.client: Optional[BleakClient] = None

        self._notify_started = False
        self._inbuf = bytearray()
        self._queue: "asyncio.Queue[BaseMessage]" = asyncio.Queue()

        self._pending: Optional[tuple[int, asyncio.Future[BaseMessage], Type[BaseMessage]]] = None
        self._lock = asyncio.Lock()

        self.info: Optional[InfoResponse] = None
        self._service_uuid = UUID.SERVICE.lower()

    # ---------- lifecycle ----------

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.disconnect()

    async def _pick_device(self):
        if self.address:
            return self.address

        def by_service(dev, adv):
            return any(u.lower() == self._service_uuid for u in (adv.service_uuids or []))

        dev = await BleakScanner.find_device_by_filter(by_service, timeout=self.timeout)
        if dev:
            return dev

        # fallback: full scan and backend details (if present)
        for d in await BleakScanner.discover(timeout=self.timeout):
            details = getattr(d, "details", None)
            uuids = (details.get("uuids") or []) if isinstance(details, dict) else []
            if any(u.lower() == self._service_uuid for u in uuids):
                return d

        raise RuntimeError(f"No SPIKE hub found advertising {self._service_uuid}")

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
        svc_uuids = {s.uuid.lower() for s in services}
        if self._service_uuid not in svc_uuids:
            await client.disconnect()
            raise RuntimeError("SPIKE App 3 service not found")

        chars = {c.uuid.lower() for s in services for c in s.characteristics}
        if UUID.RX.lower() not in chars or UUID.TX.lower() not in chars:
            await client.disconnect()
            raise RuntimeError("SPIKE RX/TX characteristics not found")

        await client.start_notify(UUID.TX, self._on_notify)
        self._notify_started = True

        self.client = client
        return client

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
                # drain message queue
                while not self._queue.empty():
                    try:
                        self._queue.get_nowait()
                        self._queue.task_done()
                    except Exception:
                        break
                # cancel any waiter
                if self._pending and not self._pending[1].done():
                    self._pending[1].cancel()
                self._pending = None

    def __del__(self):
        if self.client and getattr(self.client, "is_connected", False):
            warnings.warn("Hub was not properly disconnected.")

    # ---------- notifications ----------

    def _on_notify(self, _handle: int, data: bytes):
        buf = self._inbuf
        buf.extend(data)
        while True:
            try:
                i = buf.index(DELIMITER)
            except ValueError:
                break
            frame = bytes(buf[: i + 1])
            del buf[: i + 1]
            try:
                payload = cobs_unpack(frame)
                msg = msg_deserialize(payload)
            except Exception:
                continue
            self._dispatch(msg)

    def _dispatch(self, msg: BaseMessage):
        # pending typed response
        if self._pending and self._pending[0] == getattr(msg.__class__, "ID", -1):
            _, fut, _typ = self._pending
            if not fut.done():
                fut.set_result(msg)
                return
        # general inbox
        try:
            self._queue.put_nowait(msg)
        except Exception:
            pass

    # ---------- I/O ----------

    async def _write_frame(self, frame: bytes):
        if not self.client or not self.client.is_connected:
            raise RuntimeError("Not connected")
        packet_size = getattr(self.info, "max_packet_size", None) or len(frame)
        for off in range(0, len(frame), packet_size):
            await self.client.write_gatt_char(UUID.RX, frame[off:off + packet_size], response=False)

    async def send_message(self, message: BaseMessage) -> None:
        frame = cobs_pack(message.serialize())
        await self._write_frame(frame)

    async def send_request(self, message: BaseMessage, response_type: Type[TM], timeout: float = 5.0) -> TM:
        async with self._lock:
            if self._pending and not self._pending[1].done():
                raise RuntimeError("Another request is pending")
            fut: asyncio.Future[BaseMessage] = asyncio.get_event_loop().create_future()
            exp_id = getattr(response_type, "ID", None)
            if exp_id is None:
                raise RuntimeError("response_type must define class attribute ID")
            self._pending = (exp_id, fut, response_type)
            try:
                await self.send_message(message)
                res = await asyncio.wait_for(fut, timeout=timeout)
                if not isinstance(res, response_type):
                    # Defensive cast if user’s deserialize returns subclasses
                    return response_type.deserialize(res.serialize())  # type: ignore
                return res  # type: ignore[return-value]
            finally:
                self._pending = None

    async def recv(self, timeout: Optional[float] = None) -> BaseMessage:
        if timeout is None:
            return await self._queue.get()
        return await asyncio.wait_for(self._queue.get(), timeout=timeout)

    # ---------- high-level ops ----------

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
        """
        StartFileUpload -> TransferChunk* -> ProgramFlow(start)
        Uses running CRC over chunks (aligned inside crc()).
        """
        # negotiate sizes if needed
        if not self.info:
            await self.get_info()
        max_chunk = self.info.max_chunk_size

        total_crc = crc(data, 0)
        _ = await self.send_request(StartFileUploadRequest(name, slot, total_crc), StartFileUploadResponse, timeout=10.0)

        running = 0
        for off in range(0, len(data), max_chunk):
            chunk = data[off:off + max_chunk]
            running = crc(chunk, running)
            _ = await self.send_request(TransferChunkRequest(running, chunk), TransferChunkResponse, timeout=10.0)

        # start it
        _ = await self.start_program(slot)


# -------- demo --------
if __name__ == "__main__":

    async def main():
        async with Hub() as hub:
            info = await hub.get_info()
            print(f"Info: rpc={info.rpc_major}.{info.rpc_minor} max_packet={info.max_packet_size} max_chunk={info.max_chunk_size}")

            resp = await hub.enable_notifications(50)
            print("DeviceNotificationResponse:", getattr(resp, "success", None))

            # stream a few unsolicited messages
            for _ in range(5):
                try:
                    m = await hub.recv(timeout=3)
                    print(m)
                except asyncio.TimeoutError:
                    print("timeout")

    asyncio.run(main())