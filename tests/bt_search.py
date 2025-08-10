import asyncio
import os
import platform
from bleak import BleakScanner

def clear_terminal():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")

def format_table(devices):
    if not devices:
        return "No BLE devices found."
    headers = ["Name", "Address", "UUIDs"]
    rows = []
    for (name, address), uuids in sorted(devices.items(), key=lambda x: x[0][1]):
        rows.append([
            name or "?",
            address,
            "\n".join(uuids)
        ])
    col_widths = [max(len(str(row[i])) for row in rows + [headers]) for i in range(3)]
    sep = "+-" + "-+-".join("-" * w for w in col_widths) + "-+"
    header_row = "| " + " | ".join(headers[i].ljust(col_widths[i]) for i in range(3)) + " |"
    lines = [sep, header_row, sep]
    for row in rows:
        lines.append("| " + " | ".join(str(row[i]).ljust(col_widths[i]) for i in range(3)) + " |")
        lines.append(sep)
    return "\n".join(lines)

async def continual_scan(refresh=2.0):
    devices = {}
    while True:
        found = {}

        def cb(device, adv_data):
            uuids = list(adv_data.service_uuids or [])
            if not uuids:
                details = getattr(device, "details", None)
                if isinstance(details, dict):
                    uuids = list(details.get("uuids") or [])
            if not uuids:
                return
            key = (device.name, device.address)
            found[key] = sorted([u.lower() for u in uuids])

        scanner = BleakScanner(detection_callback=cb)
        await scanner.start()
        await asyncio.sleep(refresh)
        await scanner.stop()

        devices = found
        clear_terminal()
        print(format_table(devices))

if __name__ == "__main__":
    try:
        asyncio.run(continual_scan())
    except KeyboardInterrupt:
        pass
