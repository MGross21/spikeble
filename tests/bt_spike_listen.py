# bt_spike_live.py
import os
import asyncio
from bleak import BleakClient



# SPIKE App 3 GATT
SERVICE = "0000fd02-0000-1000-8000-00805f9b34fb"
RX = "0000fd02-0001-1000-8000-00805f9b34fb"
TX = "0000fd02-0002-1000-8000-00805f9b34fb"

ADDR = os.getenv("SPIKE_ADDR", "3C:E4:B0:AB:D3:3A")  # set env or edit here

# Use your project’s COBS helpers. Fallbacks are provided if import fails.
try:
    from ..lego_spike.lib import pack as cobs_pack, unpack as cobs_unpack
except Exception:
    # Minimal SPIKE-variant COBS (XOR 0x03, delim 0x02)
    DELIMITER = 0x02
    XOR = 0x03
    MAX_BLOCK = 84
    COBS_CODE_OFFSET = DELIMITER
    NO_DELIM = 0xFF

    def _encode(payload: bytes) -> bytearray:
        out = bytearray()
        code_index = 0
        block = 0

        def begin():
            nonlocal code_index, block
            code_index = len(out)
            out.append(NO_DELIM)
            block = 1

        begin()
        for b in payload:
            if b > DELIMITER:
                out.append(b); block += 1
            if b <= DELIMITER or block > MAX_BLOCK:
                if b <= DELIMITER:
                    base = b * MAX_BLOCK
                    out[code_index] = base + (block + COBS_CODE_OFFSET)
                begin()
        out[code_index] = block + COBS_CODE_OFFSET
        return out

    def cobs_pack(data: bytes) -> bytes:
        buf = _encode(data)
        for i in range(len(buf)):
            buf[i] ^= XOR
        buf.append(DELIMITER)
        return bytes(buf)

    def cobs_unpack(frame: bytes) -> bytes:
        start = 0
        if frame[0] == 0x01:
            start = 1
        raw = bytes(x ^ XOR for x in frame[start:-1])
        # decode
        out = bytearray()
        def unesc(code: int):
            if code == NO_DELIM:
                return None, MAX_BLOCK + 1
            v, blk = divmod(code - COBS_CODE_OFFSET, MAX_BLOCK)
            if blk == 0:
                blk = MAX_BLOCK
                v -= 1
            return v, blk
        v, blk = unesc(raw[0])
        for b in raw[1:]:
            blk -= 1
            if blk > 0:
                out.append(b); continue
            if v is not None:
                out.append(v)
            v, blk = unesc(b)
        return bytes(out)


async def main():
    async with BleakClient(ADDR) as client:
        if not client.is_connected:
            raise RuntimeError("Failed to connect")
        print("Connected:", ADDR)

        # verify service and chars exist
        services = client.services if hasattr(client, "services") else await client.get_services()
        svc_uuids = {s.uuid.lower() for s in services}
        if SERVICE not in svc_uuids:
            raise RuntimeError("SPIKE App 3 service not found")
        chars = {c.uuid.lower() for s in services for c in s.characteristics}
        if RX not in chars or TX not in chars:
            raise RuntimeError("SPIKE RX/TX characteristics not found")

        # notification handler + simple deframer using your unpack()
        inbox = asyncio.Queue()

        def on_notify(_, data: bytes):
            # split on delimiter 0x02 and unpack each subframe
            DELIM = 0x02
            # accumulate across calls
            if not hasattr(on_notify, "buf"):
                on_notify.buf = bytearray()
            on_notify.buf.extend(data)
            while True:
                try:
                    i = on_notify.buf.index(DELIM)
                except ValueError:
                    break
                frame = bytes(on_notify.buf[:i+1])
                del on_notify.buf[:i+1]
                try:
                    payload = cobs_unpack(frame)
                except Exception:
                    continue
                inbox.put_nowait(payload)

        await client.start_notify(TX, on_notify)

        # 1) InfoRequest (0x00)
        await client.write_gatt_char(RX, cobs_pack(b"\x00"), response=False)

        # Print the InfoResponse if received
        try:
            msg = await asyncio.wait_for(inbox.get(), timeout=2.0)
            if msg and msg[0] == 0x01:
                rpc = f"{msg[1]}.{msg[2]}"
                max_packet = int.from_bytes(msg[7:9], "little")
                max_chunk = int.from_bytes(msg[11:13], "little")
                print(f"InfoResponse rpc={rpc} max_packet={max_packet} max_chunk={max_chunk}")
            else:
                print("First RX:", msg.hex() if msg else None)
        except asyncio.TimeoutError:
            print("No InfoResponse")

        # 2) Enable DeviceNotifications every 50 ms: message 0x28, little-endian period
        await client.write_gatt_char(RX, cobs_pack(bytes([0x28]) + (50).to_bytes(2, "little")), response=False)
        print("Notifications enabled at 50 ms. Streaming…  Ctrl+C to stop.")

        # 3) Stream until Ctrl+C
        try:
            while True:
                msg = await inbox.get()
                # Optional minimal parse
                if msg[0] == 0x29:
                    print("DeviceNotificationResponse:", msg.hex())
                elif msg[0] == 0x3C:
                    length = int.from_bytes(msg[1:3], "little")
                    print(f"DeviceNotification len={length}")
                else:
                    print("RX:", msg.hex())
        except KeyboardInterrupt:
            print("\nStopping…")
        finally:
            await client.stop_notify(TX)

if __name__ == "__main__":
    asyncio.run(main())
