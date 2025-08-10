class UUID:
    """
    The LEGO SPIKE Prime Hub exposes a BLE GATT service with two characteristics:
    - RX: for receiving data (from the hub's perspective)
    - TX: for transmitting data (from the hub's perspective)
    """
    _BASE = "0000FD02"
    _TAIL = "1000-8000-00805F9B34FB"
    SERVICE = f"{_BASE}-0000-{_TAIL}"
    RX = f"{_BASE}-0001-{_TAIL}"
    TX = f"{_BASE}-0002-{_TAIL}"

class Hardware:
    MAC_ADDR = "3C:E4:B0:AB:D3:3A"

class Name:
    HINTS = [
        "SPIKE",
        "Spike",
        "Prime",
        "Hub",
        "Lego"
    ] + [str(i) for i in range(1, 100)]