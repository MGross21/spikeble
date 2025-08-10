from __future__ import annotations
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
import warnings
import textwrap
import inspect
from typing import Optional, Type, TypeVar

from bleak import BleakScanner, BleakClient
from bleak.exc import BleakError

from lib.connection import UUID, Name  # optional defaults/hints
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
    """SPIKE Prime hub over SPIKE App 3 BLE. Dynamic service/characteristic resolution."""

    # Accept lists to permit future variants. Defaults use lib.connection.UUID.
    SERVICE_UUIDS = [UUID.SERVICE.lower()]
    RX_UUIDS = [UUID.RX.lower()]
    TX_UUIDS = [UUID.TX.lower()]

    NAME_HINTS = [h.lower() for h in getattr(Name, "HINTS", [])]

    def __init__(self, *, address: Optional[str] = None, timeout: float = 15.0):
        self.timeout = timeout
        self.address = address
        self.client: Optional[BleakClient] = None

        self._service_uuid: Optional[str] = None
        self._rx_uuid: Optional[str] = None
        self._tx_uuid: Optional[str] = None
        self._rx_props: set[str] = set()

        self._notify_started = False
        self._inbuf = bytearray()
        self._queue: "asyncio.Queue[BaseMessage]" = asyncio.Queue()

        self._pending: Optional[tuple[int, asyncio.Future[BaseMessage], type[BaseMessage]]] = None
        self._lock = asyncio.Lock()
        self.info: Optional[InfoResponse] = None

    # ---- context ----

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.disconnect()

    # ---- discovery ----

    async def _pick_device(self):
        """Find device by explicit address, service UUID, or name hints."""
        if self.address:
            return self.address

        known_services = set(self.SERVICE_UUIDS)

        def by_adv(dev, adv):
            uuids = [u.lower() for u in (adv.service_uuids or [])]
            if any(u in known_services for u in uuids):
                return True
            name = (dev.name or "").lower()
            return any(h in name for h in self.NAME_HINTS)

        dev = await BleakScanner.find_device_by_filter(by_adv, timeout=self.timeout)
        if dev:
            return dev

        # Fallback: full discovery
        devices = await BleakScanner.discover(timeout=self.timeout)
        for d in devices:
            name = (getattr(d, "name", "") or "").lower()
            if any(h in name for h in self.NAME_HINTS):
                return d
        raise RuntimeError("No SPIKE hub found")

    async def _resolve_uuids(self, client: BleakClient):
        # Modern Bleak: services are available after connection
        services = client.services
        if services is None:
            raise RuntimeError("GATT services not available from Bleak client")

        # Strict: prefer the known FD02 service
        svc = None
        for s in services:
            if s.uuid.lower() in self.SERVICE_UUIDS:
                svc = s
                break
        
        if not svc:
            # Fallback: pick a service that has at least one notifiable and one writable characteristic
            candidate = None
            for s in services:
                has_notify = any("notify" in c.properties for c in s.characteristics)
                has_write = any(prop in c.properties for prop in ["write", "write-without-response"] 
                               for c in s.characteristics)
                if has_notify and has_write:
                    candidate = s
                    break
            if not candidate:
                raise RuntimeError("SPIKE service not found")
            svc = candidate

        # Try exact UUIDs first
        rx = None
        tx = None
        for c in svc.characteristics:
            if c.uuid.lower() in self.RX_UUIDS:
                rx = c
            if c.uuid.lower() in self.TX_UUIDS:
                tx = c

        # Fallback by properties, enforce distinct chars
        if not rx or not tx:
            for ch in svc.characteristics:
                props = ch.properties
                if not tx and "notify" in props:
                    tx = ch
                if not rx and any(prop in props for prop in ["write", "write-without-response"]):
                    if not tx or ch.uuid != tx.uuid:
                        rx = ch

        if not rx or not tx:
            raise RuntimeError("RX/TX characteristics not found")
        if rx.uuid == tx.uuid:
            raise RuntimeError("Resolved RX and TX to the same characteristic")

        rx_props = set(rx.properties)
        if not any(prop in rx_props for prop in ["write", "write-without-response"]):
            raise RuntimeError("Mapped RX not writable")
        if "notify" not in tx.properties:
            raise RuntimeError("Mapped TX not notifiable")

        self._service_uuid = svc.uuid
        self._rx_uuid, self._tx_uuid = rx.uuid, tx.uuid
        self._rx_props = rx_props

    # ---- connection ----

    async def connect(self):
        target = await self._pick_device()
        client = BleakClient(target)
        try:
            await client.connect()
        except BleakError as e:
            raise RuntimeError("Bluetooth connect failed") from e
        if not client.is_connected:
            raise RuntimeError("Bluetooth connect failed")

        # Modern Bleak automatically discovers services on connection
        # No need to explicitly call get_services()

        await self._resolve_uuids(client)

        await client.start_notify(self._tx_uuid, self._on_notify)
        self._notify_started = True
        await asyncio.sleep(0.3)  # allow CCCD to settle on some stacks

        self.client = client
        return client

    async def disconnect(self):
        if not self.client:
            return
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

    def _on_notify(self, _sender, data: bytes):
        """Handle notification callback. Modern Bleak passes sender instead of handle."""
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

    # ---- write/read ----

    async def _write_frame(self, frame: bytes):
        if not self.client or not self.client.is_connected or not self._rx_uuid:
            raise RuntimeError("Not connected")
        if not any(prop in self._rx_props for prop in ["write", "write-without-response"]):
            raise RuntimeError("Current RX not writable")

        packet_size = getattr(self.info, "max_packet_size", None) or len(frame)
        use_resp = "write" in self._rx_props
        for off in range(0, len(frame), packet_size):
            chunk = frame[off: off + packet_size]
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
            chunk = data[off: off + max_chunk]
            running = crc(chunk, running)
            _ = await self.send_request(
                TransferChunkRequest(running, chunk),
                TransferChunkResponse,
                timeout=10.0,
            )
        _ = await self.start_program(slot)
    
    # ---- convenience runners ----
    
    async def run_source(self, *, slot: int, name: str = "main.py", source: str,
                         follow_seconds: Optional[float] = None) -> None:
        """Run Python source code on the hub with optimized execution flow.
        
        Args:
            slot: Program slot number (0-19)
            name: Program name (default: "main.py")
            source: Python source code to execute
            follow_seconds: Time to monitor output (None = no monitoring)
        """
        data = source.encode("utf-8")
        
        # Batch operations for efficiency
        await self.clear_slot(slot)
        await self.upload_program(slot=slot, name=name, data=data)
        
        if follow_seconds is not None:
            await self._follow_execution(follow_seconds)

    async def run_file(self, *, slot: int, path: str, name: Optional[str] = None,
                       follow_seconds: Optional[float] = None) -> None:
        """Run Python file on the hub with optimized file handling.
        
        Args:
            slot: Program slot number (0-19)  
            path: Path to Python file
            name: Program name (default: basename of path)
            follow_seconds: Time to monitor output (None = no monitoring)
        """
        # Read file efficiently
        try:
            with open(path, "rb") as f:
                data = f.read()
        except IOError as e:
            raise RuntimeError(f"Failed to read file {path}: {e}") from e
        
        program_name = name or os.path.basename(path)
        
        # Batch operations for efficiency
        await self.clear_slot(slot)
        await self.upload_program(slot=slot, name=program_name, data=data)
        
        if follow_seconds is not None:
            await self._follow_execution(follow_seconds)

    async def run_func(self, *, slot: int, fn: Callable[[], Any], name: str = "main.py",
                       follow_seconds: Optional[float] = None) -> None:
        """Run Python function on the hub with optimized source extraction.
        
        Args:
            slot: Program slot number (0-19)
            fn: Python function to execute (must be callable with no args)
            name: Program name (default: "main.py") 
            follow_seconds: Time to monitor output (None = no monitoring)
        """
        try:
            # Extract and prepare source code
            src = textwrap.dedent(inspect.getsource(fn))
            entry = f"\nif __name__ == '__main__':\n    {fn.__name__}()\n"
            complete_source = src + entry
        except OSError as e:
            raise RuntimeError(f"Failed to extract source for function {fn.__name__}: {e}") from e
        
        await self.run_source(slot=slot, name=name, source=complete_source,
                              follow_seconds=follow_seconds)

    async def _follow_execution(self, follow_seconds: float) -> None:
        """Optimized execution monitoring with precise timing."""
        # Enable notifications once
        try:
            await self.enable_notifications(50)
        except Exception as e:
            print(f"Warning: Could not enable notifications: {e}")
            return
        
        # Use high-precision timing
        end_time = asyncio.get_event_loop().time() + follow_seconds
        
        try:
            while True:
                remaining = end_time - asyncio.get_event_loop().time()
                if remaining <= 0:
                    break
                
                try:
                    msg = await self.recv(timeout=min(remaining, 1.0))  # Cap individual waits
                    print(msg)
                except asyncio.TimeoutError:
                    # Check if we've exceeded total time
                    if asyncio.get_event_loop().time() >= end_time:
                        break
                    continue
                except Exception as e:
                    print(f"Error receiving message: {e}")
                    break
        except KeyboardInterrupt:
            print("\nMonitoring interrupted by user")
        except Exception as e:
            print(f"Error during execution monitoring: {e}")

    async def run_and_wait(self, *, slot: int, source: str, name: str = "main.py", 
                          timeout: float = 30.0) -> list[BaseMessage]:
        """Run code and collect all output messages until completion.
        
        Args:
            slot: Program slot number (0-19)
            source: Python source code
            name: Program name
            timeout: Maximum time to wait for completion
            
        Returns:
            List of all messages received during execution
        """
        messages = []
        data = source.encode("utf-8")
        
        # Prepare execution
        await self.clear_slot(slot)
        await self.enable_notifications(50)  # Enable before upload
        await self.upload_program(slot=slot, name=name, data=data)
        
        # Collect messages with timeout
        end_time = asyncio.get_event_loop().time() + timeout
        no_message_timeout = 2.0  # Stop if no message for 2 seconds
        last_message_time = asyncio.get_event_loop().time()
        
        try:
            while True:
                now = asyncio.get_event_loop().time()
                remaining = end_time - now
                no_msg_remaining = last_message_time + no_message_timeout - now
                
                if remaining <= 0:
                    break
                
                wait_time = min(remaining, max(0.1, no_msg_remaining))
                
                try:
                    msg = await self.recv(timeout=wait_time)
                    messages.append(msg)
                    last_message_time = now
                except asyncio.TimeoutError:
                    # Check if we should stop due to no messages
                    if now >= last_message_time + no_message_timeout:
                        break
                    if remaining <= 0:
                        break
                    continue
                        
        except Exception as e:
            print(f"Error during execution: {e}")
        
        return messages


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