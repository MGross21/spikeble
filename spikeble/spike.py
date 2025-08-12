from __future__ import annotations
import asyncio
import logging
from typing import Callable, Awaitable, Optional, Tuple, Type, TypeVar, cast

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from bleak.backends.characteristic import BleakGATTCharacteristic

from ._lib.connection import UUID
from ._lib import cobs
from ._lib.crc import crc
from ._lib.messages import *  # BaseMessage, InfoRequest, InfoResponse, etc.

TM = TypeVar("TM", bound="BaseMessage")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


class Spike:
    DEVICE_NOTIFICATION_INTERVAL_MS = 5000

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, timeout: int = 10, slot: int = 0) -> None:
        self.timeout = timeout
        self.slot = slot

        self._device: Optional[BLEDevice] = None
        self._client: Optional[BleakClient] = None
        self._service = None
        self._rx = None
        self._tx = None

        self._stop = asyncio.Event()
        self._info: Optional[InfoResponse] = None
        self._pending: Tuple[int, asyncio.Future] = (-1, asyncio.Future())
        self._notify_cb: Optional[
            Callable[[DeviceNotification], Awaitable[None] | None]
        ] = None

    async def connect(self) -> None:
        self._device = await BleakScanner.find_device_by_filter(
            filterfunc=self._match_service, timeout=self.timeout
        )
        if self._device is None:
            logger.error(
                "No SPIKE hub found. Ensure power, range, and pairing state."
            )
            raise RuntimeError("No SPIKE hub found")

        logger.info("Connecting to SPIKE hub...")
        self._client = BleakClient(
            self._device, disconnected_callback=self._on_disconnect
        )
        await self._client.connect()

        # Some Bleak builds don’t have get_services(); services are available post-connect.
        # If your build does have it, calling it is harmless. Guard with hasattr.
        if hasattr(self._client, "get_services"):
            try:
                await getattr(
                    self._client, "get_services"
                )()  # no-op on some backends
            except TypeError:
                # Older signatures or property-only; ignore
                pass

        svc = self._client.services.get_service(UUID.SERVICE)
        if svc is None:
            raise RuntimeError(
                "SPIKE service not found on the connected device"
            )

        self._service = svc
        self._rx = svc.get_characteristic(UUID.RX)
        self._tx = svc.get_characteristic(UUID.TX)
        if not self._rx or not self._tx:
            raise RuntimeError("SPIKE RX/TX characteristics not found")

        await self._client.start_notify(self._tx, self._on_data)
        logger.info("Connected to SPIKE hub")

    async def disconnect(self) -> None:
        if self._client and self._client.is_connected:
            await self._client.disconnect()
            logger.info("Disconnected from SPIKE hub")

    async def get_info(self) -> InfoResponse:
        logger.info("Requesting hub info...")
        self._info = await self._send_request(InfoRequest(), InfoResponse)
        logger.info(f"Hub info: {self._info}")
        return self._info

    async def enable_notifications(
        self, interval_ms: int = DEVICE_NOTIFICATION_INTERVAL_MS
    ) -> None:
        logger.info(f"Enabling device notifications every {interval_ms} ms")
        resp = await self._send_request(
            DeviceNotificationRequest(interval_ms), DeviceNotificationResponse
        )
        if not resp.success:
            logger.error("Failed to enable notifications")
            raise RuntimeError("Failed to enable notifications")
        logger.info("Device notifications enabled")

    async def clear_slot(self, slot: Optional[int] = None) -> None:
        s = self.slot if slot is None else slot
        logger.info(f"Clearing slot {s}")
        resp = await self._send_request(ClearSlotRequest(s), ClearSlotResponse)
        if not resp.success:
            logger.warning(
                f"Slot {s} not acknowledged as cleared (may already be empty)"
            )

    async def upload_program(
        self,
        program: bytes,
        name: str = "program.py",
        slot: Optional[int] = None,
    ) -> None:
        s = self.slot if slot is None else slot
        info = self._require_info()

        logger.info(f"Starting file upload to slot {s} as '{name}'")
        start = await self._send_request(
            StartFileUploadRequest(name, s, crc(program)),
            StartFileUploadResponse,
        )
        if not start.success:
            logger.error("StartFileUpload not acknowledged")
            raise RuntimeError("StartFileUpload not acknowledged")

        running_crc = 0
        for i in range(0, len(program), info.max_chunk_size):
            chunk = program[i : i + info.max_chunk_size]
            running_crc = crc(chunk, running_crc)
            part = await self._send_request(
                TransferChunkRequest(running_crc, chunk), TransferChunkResponse
            )
            if not part.success:
                logger.error(f"Chunk transfer failed at offset {i}")
                raise RuntimeError(f"Chunk transfer failed at offset {i}")
        logger.info("File upload complete")

    async def start_program(self, slot: Optional[int] = None) -> None:
        s = self.slot if slot is None else slot
        logger.info(f"Starting program in slot {s}")
        resp = await self._send_request(
            ProgramFlowRequest(stop=False, slot=s), ProgramFlowResponse
        )
        if not resp.success:
            logger.error("Failed to start program")
            raise RuntimeError("Failed to start program")
        logger.info("Program started")

    async def run_until_disconnect(self) -> None:
        logger.info("Waiting until disconnect...")
        await self._stop.wait()

    def on_device_notification(
        self, cb: Callable[[DeviceNotification], Awaitable[None] | None]
    ) -> None:
        self._notify_cb = cb

    async def __aenter__(self) -> Spike:
        await self.connect()
        return self

    async def __aexit__(self, _, __, ___) -> None:
        await self.disconnect()

    @staticmethod
    def _match_service(_dev: BLEDevice, adv: AdvertisementData) -> bool:
        uuids = adv.service_uuids or []
        return UUID.SERVICE.lower() in [u.lower() for u in uuids]

    def _on_disconnect(self, _client: BleakClient) -> None:
        logger.warning("SPIKE hub disconnected")
        self._stop.set()

    async def _send(self, msg: BaseMessage) -> None:
        if not self._client or not self._rx:
            raise RuntimeError("Not connected")

        logger.debug(f"Sending: {msg}")
        payload = msg.serialize()
        frame = cobs.pack(payload)
        packet_size = self._info.max_packet_size if self._info else len(frame)

        for i in range(0, len(frame), packet_size):
            await self._client.write_gatt_char(
                self._rx, frame[i : i + packet_size], response=False
            )

    async def _send_request(self, msg: BaseMessage, resp_t: Type[TM]) -> TM:
        loop = asyncio.get_event_loop()
        self._pending = (resp_t.ID, loop.create_future())
        await self._send(msg)
        return cast(TM, await self._pending[1])

    def _on_data(self, _ch: BleakGATTCharacteristic, data: bytearray) -> None:
        if not data or data[-1] != cobs.DELIMITER:
            try:
                un_xor = bytes(b ^ cobs.XOR for b in data)
                logger.warning(f"Incomplete message:\n {un_xor}")
            except Exception:
                logger.warning("Incomplete message (unpack failed)")
            return

        try:
            msg = deserialize(cobs.unpack(data))
            logger.debug(f"Received: {msg}")
        except Exception as e:
            logger.error(f"Decode error: {e}")
            return

        if msg.ID == self._pending[0] and not self._pending[1].done():
            self._pending[1].set_result(msg)

        if isinstance(msg, DeviceNotification):
            if self._notify_cb:
                res = self._notify_cb(msg)
                if asyncio.iscoroutine(res):
                    asyncio.create_task(res)
            else:
                updates = sorted(msg.messages, key=lambda x: x[1])
                for name, value in updates:
                    logger.info(f" - {name:<10}: {value}")

    def _require_info(self) -> InfoResponse:
        if self._info is None:
            raise RuntimeError("Call get_info() first")
        return self._info
