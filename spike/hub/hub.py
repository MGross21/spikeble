from __future__ import annotations
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Modular Hub Architecture
import asyncio
import warnings
import textwrap
import inspect
from typing import Optional, Type, TypeVar, Callable, Any, Protocol
from abc import ABC, abstractmethod

from bleak import BleakScanner, BleakClient
from bleak.exc import BleakError

from lib.connection import UUID, Name
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


# ---- Protocol Definitions ----

class MessageHandler(Protocol):
    async def handle(self, message: BaseMessage) -> None: ...


class ConnectionEventHandler(Protocol):
    async def on_connect(self) -> None: ...
    async def on_disconnect(self) -> None: ...


# ---- Core Components ----

class DeviceDiscovery:
    """Handles BLE device discovery and filtering."""
    
    def __init__(self, service_uuids: list[str], name_hints: list[str], timeout: float = 15.0):
        self.service_uuids = [uuid.lower() for uuid in service_uuids]
        self.name_hints = [hint.lower() for hint in name_hints]
        self.timeout = timeout

    async def find_device(self, address: Optional[str] = None):
        """Find device by explicit address, service UUID, or name hints."""
        if address:
            return address

        known_services = set(self.service_uuids)

        def by_adv(dev, adv):
            uuids = [u.lower() for u in (adv.service_uuids or [])]
            if any(u in known_services for u in uuids):
                return True
            name = (dev.name or "").lower()
            return any(h in name for h in self.name_hints)

        dev = await BleakScanner.find_device_by_filter(by_adv, timeout=self.timeout)
        if dev:
            return dev

        # Fallback: full discovery
        devices = await BleakScanner.discover(timeout=self.timeout)
        for d in devices:
            name = (getattr(d, "name", "") or "").lower()
            if any(h in name for h in self.name_hints):
                return d
        raise RuntimeError("No SPIKE hub found")


class ServiceResolver:
    """Handles GATT service and characteristic resolution."""
    
    def __init__(self, service_uuids: list[str], rx_uuids: list[str], tx_uuids: list[str]):
        self.service_uuids = [uuid.lower() for uuid in service_uuids]
        self.rx_uuids = [uuid.lower() for uuid in rx_uuids]
        self.tx_uuids = [uuid.lower() for uuid in tx_uuids]

    async def resolve(self, client: BleakClient) -> tuple[str, str, str, set[str]]:
        """Returns (service_uuid, rx_uuid, tx_uuid, rx_props)"""
        services = client.services
        if services is None:
            raise RuntimeError("GATT services not available")

        svc = self._find_service(services)
        rx_char, tx_char = self._find_characteristics(svc)
        
        self._validate_characteristics(rx_char, tx_char)
        
        return svc.uuid, rx_char.uuid, tx_char.uuid, set(rx_char.properties)

    def _find_service(self, services):
        # Try known service UUIDs first
        for s in services:
            if s.uuid.lower() in self.service_uuids:
                return s
        
        # Fallback: find service with required characteristics
        for s in services:
            has_notify = any("notify" in c.properties for c in s.characteristics)
            has_write = any(prop in c.properties for prop in ["write", "write-without-response"] 
                           for c in s.characteristics)
            if has_notify and has_write:
                return s
        
        raise RuntimeError("SPIKE service not found")

    def _find_characteristics(self, service):
        rx = tx = None
        
        # Try exact UUIDs first
        for c in service.characteristics:
            if c.uuid.lower() in self.rx_uuids:
                rx = c
            if c.uuid.lower() in self.tx_uuids:
                tx = c

        # Fallback by properties
        if not rx or not tx:
            for ch in service.characteristics:
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
            
        return rx, tx

    def _validate_characteristics(self, rx_char, tx_char):
        rx_props = set(rx_char.properties)
        if not any(prop in rx_props for prop in ["write", "write-without-response"]):
            raise RuntimeError("Mapped RX not writable")
        if "notify" not in tx_char.properties:
            raise RuntimeError("Mapped TX not notifiable")


class MessageDispatcher:
    """Handles message parsing, dispatching, and queuing."""
    
    def __init__(self):
        self._inbuf = bytearray()
        self._queue: asyncio.Queue[BaseMessage] = asyncio.Queue()
        self._pending: Optional[tuple[int, asyncio.Future[BaseMessage], type[BaseMessage]]] = None
        self._handlers: list[MessageHandler] = []

    def add_handler(self, handler: MessageHandler):
        """Add a message handler."""
        self._handlers.append(handler)

    def remove_handler(self, handler: MessageHandler):
        """Remove a message handler."""
        if handler in self._handlers:
            self._handlers.remove(handler)

    def on_notify(self, _sender, data: bytes):
        """Handle incoming BLE notification data."""
        self._inbuf.extend(data)
        while True:
            try:
                i = self._inbuf.index(DELIMITER)
            except ValueError:
                break
            frame = bytes(self._inbuf[:i + 1])
            del self._inbuf[:i + 1]
            try:
                payload = cobs_unpack(frame)
                msg = msg_deserialize(payload)
                self._dispatch(msg)
            except Exception:
                continue

    def _dispatch(self, msg: BaseMessage):
        """Dispatch message to pending request or queue."""
        # Handle pending requests first
        if self._pending and self._pending[0] == getattr(msg.__class__, "ID", -1):
            _, fut, _ = self._pending
            if not fut.done():
                fut.set_result(msg)
                return
        
        # Queue message for general consumption
        self._queue.put_nowait(msg)
        
        # Notify handlers asynchronously
        for handler in self._handlers:
            asyncio.create_task(handler.handle(msg))

    async def recv(self, timeout: Optional[float] = None) -> BaseMessage:
        """Receive next message from queue."""
        if timeout is None:
            return await self._queue.get()
        return await asyncio.wait_for(self._queue.get(), timeout=timeout)

    def set_pending(self, msg_id: int, future: asyncio.Future[BaseMessage], response_type: type[BaseMessage]):
        """Set pending request expectation."""
        if self._pending and not self._pending[1].done():
            raise RuntimeError("Another request is pending")
        self._pending = (msg_id, future, response_type)

    def clear_pending(self):
        """Clear pending request."""
        if self._pending and not self._pending[1].done():
            self._pending[1].cancel()
        self._pending = None

    def cleanup(self):
        """Clean up resources."""
        self._inbuf.clear()
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except Exception:
                break
        self.clear_pending()


class BLEConnection:
    """Manages BLE connection lifecycle and communication."""
    
    def __init__(self, discovery: DeviceDiscovery, resolver: ServiceResolver, dispatcher: MessageDispatcher):
        self.discovery = discovery
        self.resolver = resolver
        self.dispatcher = dispatcher
        
        self.client: Optional[BleakClient] = None
        self._service_uuid: Optional[str] = None
        self._rx_uuid: Optional[str] = None
        self._tx_uuid: Optional[str] = None
        self._rx_props: set[str] = set()
        self._notify_started = False
        self._event_handlers: list[ConnectionEventHandler] = []

    def add_event_handler(self, handler: ConnectionEventHandler):
        """Add connection event handler."""
        self._event_handlers.append(handler)

    async def connect(self, address: Optional[str] = None):
        """Establish BLE connection."""
        target = await self.discovery.find_device(address)
        client = BleakClient(target)
        
        try:
            await client.connect()
        except BleakError as e:
            raise RuntimeError("Bluetooth connect failed") from e
        
        if not client.is_connected:
            raise RuntimeError("Bluetooth connect failed")

        # Resolve service characteristics
        service_uuid, rx_uuid, tx_uuid, rx_props = await self.resolver.resolve(client)
        self._service_uuid = service_uuid
        self._rx_uuid = rx_uuid
        self._tx_uuid = tx_uuid
        self._rx_props = rx_props

        # Start notifications
        await client.start_notify(self._tx_uuid, self.dispatcher.on_notify)
        self._notify_started = True
        await asyncio.sleep(0.3)  # Allow CCCD to settle

        self.client = client
        
        # Notify event handlers
        for handler in self._event_handlers:
            await handler.on_connect()
        
        return client

    async def disconnect(self):
        """Close BLE connection."""
        if not self.client:
            return
        
        try:
            # Notify event handlers first
            for handler in self._event_handlers:
                try:
                    await handler.on_disconnect()
                except Exception:
                    pass
            
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
            self.dispatcher.cleanup()

    async def write_frame(self, frame: bytes, info: Optional[InfoResponse] = None):
        """Write frame to device."""
        if not self.client or not self.client.is_connected or not self._rx_uuid:
            raise RuntimeError("Not connected")
        if not any(prop in self._rx_props for prop in ["write", "write-without-response"]):
            raise RuntimeError("Current RX not writable")

        packet_size = getattr(info, "max_packet_size", None) or len(frame)
        use_resp = "write" in self._rx_props
        
        for off in range(0, len(frame), packet_size):
            chunk = frame[off:off + packet_size]
            await self.client.write_gatt_char(self._rx_uuid, chunk, response=use_resp)

    @property
    def is_connected(self) -> bool:
        return self.client is not None and self.client.is_connected


class RequestManager:
    """Handles request/response pairs with timeout management."""
    
    def __init__(self, connection: BLEConnection, dispatcher: MessageDispatcher):
        self.connection = connection
        self.dispatcher = dispatcher
        self._lock = asyncio.Lock()

    async def send_message(self, message: BaseMessage, info: Optional[InfoResponse] = None):
        """Send message without expecting response."""
        frame = cobs_pack(message.serialize())
        await self.connection.write_frame(frame, info)

    async def send_request(self, message: BaseMessage, response_type: Type[TM], 
                          timeout: float = 5.0, info: Optional[InfoResponse] = None) -> TM:
        """Send request and wait for typed response."""
        async with self._lock:
            exp_id = getattr(response_type, "ID", None)
            if exp_id is None:
                raise RuntimeError("response_type must define ID")
            
            fut: asyncio.Future[BaseMessage] = asyncio.get_event_loop().create_future()
            self.dispatcher.set_pending(exp_id, fut, response_type)
            
            try:
                await self.send_message(message, info)
                res = await asyncio.wait_for(fut, timeout=timeout)
                return res  # type: ignore[return-value]
            finally:
                self.dispatcher.clear_pending()


class ProgramManager:
    """High-level program management operations."""
    
    def __init__(self, request_manager: RequestManager):
        self.request_manager = request_manager
        self.info: Optional[InfoResponse] = None

    async def get_info(self) -> InfoResponse:
        """Get hub information."""
        self.info = await self.request_manager.send_request(InfoRequest(), InfoResponse, timeout=5.0)
        return self.info

    async def enable_notifications(self, period_ms: int = 50) -> DeviceNotificationResponse:
        """Enable device notifications."""
        return await self.request_manager.send_request(
            DeviceNotificationRequest(period_ms), DeviceNotificationResponse, timeout=5.0)

    async def clear_slot(self, slot: int) -> ClearSlotResponse:
        """Clear program slot."""
        return await self.request_manager.send_request(ClearSlotRequest(slot), ClearSlotResponse, timeout=5.0)

    async def start_program(self, slot: int) -> ProgramFlowResponse:
        """Start program in slot."""
        return await self.request_manager.send_request(
            ProgramFlowRequest(False, slot), ProgramFlowResponse, timeout=5.0)

    async def stop_program(self, slot: int) -> ProgramFlowResponse:
        """Stop program in slot."""
        return await self.request_manager.send_request(
            ProgramFlowRequest(True, slot), ProgramFlowResponse, timeout=5.0)

    async def upload_program(self, *, slot: int, name: str, data: bytes) -> None:
        """Upload program data to slot."""
        if not self.info:
            await self.get_info()
        
        max_chunk = self.info.max_chunk_size
        total_crc = crc(data, 0)
        
        await self.request_manager.send_request(
            StartFileUploadRequest(name, slot, total_crc),
            StartFileUploadResponse,
            timeout=10.0,
            info=self.info
        )
        
        running = 0
        for off in range(0, len(data), max_chunk):
            chunk = data[off:off + max_chunk]
            running = crc(chunk, running)
            await self.request_manager.send_request(
                TransferChunkRequest(running, chunk),
                TransferChunkResponse,
                timeout=10.0,
                info=self.info
            )
        
        await self.start_program(slot)


class ExecutionRunner:
    """High-level execution convenience methods."""
    
    def __init__(self, program_manager: ProgramManager, dispatcher: MessageDispatcher):
        self.program_manager = program_manager
        self.dispatcher = dispatcher

    async def run_source(self, *, slot: int, name: str = "main.py", source: str,
                         follow_seconds: Optional[float] = None) -> None:
        """Run Python source code."""
        data = source.encode("utf-8")
        await self.program_manager.clear_slot(slot)
        await self.program_manager.upload_program(slot=slot, name=name, data=data)
        
        if follow_seconds is not None:
            await self._follow_execution(follow_seconds)

    async def run_file(self, *, slot: int, path: str, name: Optional[str] = None,
                       follow_seconds: Optional[float] = None) -> None:
        """Run Python file."""
        try:
            with open(path, "rb") as f:
                data = f.read()
        except IOError as e:
            raise RuntimeError(f"Failed to read file {path}: {e}") from e
        
        program_name = name or os.path.basename(path)
        await self.program_manager.clear_slot(slot)
        await self.program_manager.upload_program(slot=slot, name=program_name, data=data)
        
        if follow_seconds is not None:
            await self._follow_execution(follow_seconds)

    async def run_func(self, *, slot: int, fn: Callable[[], Any], name: str = "main.py",
                       follow_seconds: Optional[float] = None) -> None:
        """Run Python function."""
        try:
            src = textwrap.dedent(inspect.getsource(fn))
            entry = f"\nif __name__ == '__main__':\n    {fn.__name__}()\n"
            complete_source = src + entry
        except OSError as e:
            raise RuntimeError(f"Failed to extract source for function {fn.__name__}: {e}") from e
        
        await self.run_source(slot=slot, name=name, source=complete_source,
                              follow_seconds=follow_seconds)

    async def run_and_wait(self, *, slot: int, source: str, name: str = "main.py", 
                          timeout: float = 30.0) -> list[BaseMessage]:
        """Run code and collect all output messages."""
        messages = []
        data = source.encode("utf-8")
        
        await self.program_manager.clear_slot(slot)
        await self.program_manager.enable_notifications(50)
        await self.program_manager.upload_program(slot=slot, name=name, data=data)
        
        end_time = asyncio.get_event_loop().time() + timeout
        no_message_timeout = 2.0
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
                    msg = await self.dispatcher.recv(timeout=wait_time)
                    messages.append(msg)
                    last_message_time = now
                except asyncio.TimeoutError:
                    if now >= last_message_time + no_message_timeout or remaining <= 0:
                        break
                    continue
                        
        except Exception as e:
            print(f"Error during execution: {e}")
        
        return messages

    async def _follow_execution(self, follow_seconds: float) -> None:
        """Monitor execution output."""
        try:
            await self.program_manager.enable_notifications(50)
        except Exception as e:
            print(f"Warning: Could not enable notifications: {e}")
            return
        
        end_time = asyncio.get_event_loop().time() + follow_seconds
        
        try:
            while True:
                remaining = end_time - asyncio.get_event_loop().time()
                if remaining <= 0:
                    break
                
                try:
                    msg = await self.dispatcher.recv(timeout=min(remaining, 1.0))
                    print(msg)
                except asyncio.TimeoutError:
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


# ---- Main Hub Class ----

class Hub:
    """SPIKE Prime hub interface - composed of modular components."""
    
    def __init__(self, *, address: Optional[str] = None, timeout: float = 15.0):
        # Core configuration
        service_uuids = [UUID.SERVICE.lower()]
        rx_uuids = [UUID.RX.lower()]
        tx_uuids = [UUID.TX.lower()]
        name_hints = [h.lower() for h in getattr(Name, "HINTS", [])]
        
        # Initialize components
        self.discovery = DeviceDiscovery(service_uuids, name_hints, timeout)
        self.resolver = ServiceResolver(service_uuids, rx_uuids, tx_uuids)
        self.dispatcher = MessageDispatcher()
        self.connection = BLEConnection(self.discovery, self.resolver, self.dispatcher)
        self.request_manager = RequestManager(self.connection, self.dispatcher)
        self.program_manager = ProgramManager(self.request_manager)
        self.runner = ExecutionRunner(self.program_manager, self.dispatcher)
        
        # Store address for connection
        self.address = address

    # ---- Context Management ----
    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.disconnect()

    def __del__(self):
        if self.connection.is_connected:
            warnings.warn("Hub was not properly disconnected.")

    # ---- Connection Management ----
    async def connect(self):
        """Connect to hub."""
        return await self.connection.connect(self.address)

    async def disconnect(self):
        """Disconnect from hub."""
        await self.connection.disconnect()

    @property
    def is_connected(self) -> bool:
        return self.connection.is_connected

    # ---- Message Handling ----
    def add_message_handler(self, handler: MessageHandler):
        """Add custom message handler."""
        self.dispatcher.add_handler(handler)

    def remove_message_handler(self, handler: MessageHandler):
        """Remove message handler."""
        self.dispatcher.remove_handler(handler)

    async def send_message(self, message: BaseMessage) -> None:
        """Send message to hub."""
        await self.request_manager.send_message(message, self.program_manager.info)

    async def send_request(self, message: BaseMessage, response_type: Type[TM], timeout: float = 5.0) -> TM:
        """Send request and wait for response."""
        return await self.request_manager.send_request(message, response_type, timeout, self.program_manager.info)

    async def recv(self, timeout: Optional[float] = None) -> BaseMessage:
        """Receive message."""
        return await self.dispatcher.recv(timeout)

    # ---- Program Management (Delegated) ----
    async def get_info(self) -> InfoResponse:
        return await self.program_manager.get_info()

    async def enable_notifications(self, period_ms: int = 50) -> DeviceNotificationResponse:
        return await self.program_manager.enable_notifications(period_ms)

    async def clear_slot(self, slot: int) -> ClearSlotResponse:
        return await self.program_manager.clear_slot(slot)

    async def start_program(self, slot: int) -> ProgramFlowResponse:
        return await self.program_manager.start_program(slot)

    async def stop_program(self, slot: int) -> ProgramFlowResponse:
        return await self.program_manager.stop_program(slot)

    async def upload_program(self, *, slot: int, name: str, data: bytes) -> None:
        return await self.program_manager.upload_program(slot=slot, name=name, data=data)

    # ---- Execution Runners (Delegated) ----
    async def run_source(self, **kwargs) -> None:
        return await self.runner.run_source(**kwargs)

    async def run_file(self, **kwargs) -> None:
        return await self.runner.run_file(**kwargs)

    async def run_func(self, **kwargs) -> None:
        return await self.runner.run_func(**kwargs)

    async def run_and_wait(self, **kwargs) -> list[BaseMessage]:
        return await self.runner.run_and_wait(**kwargs)


# ---- Demo ----
if __name__ == "__main__":
    async def main():
        from lib.connection import Hardware
        async with Hub(address=getattr(Hardware, "MAC_ADDR", None)) as hub:
            try:
                info = await hub.get_info()
                print(f"Info rpc={info.rpc_major}.{info.rpc_minor} "
                      f"max_packet={info.max_packet_size} max_chunk={info.max_chunk_size}")
            except asyncio.TimeoutError:
                print("InfoRequest timed out")

            try:
                await hub.enable_notifications(50)
            except asyncio.TimeoutError:
                print("Enable notifications timed out")

            for _ in range(5):
                try:
                    m = await hub.recv(timeout=3)
                    print(m)
                except asyncio.TimeoutError:
                    print("timeout")

    asyncio.run(main())