class UUID:
    """
    The LEGO SPIKE Prime Hub exposes a BLE GATT service with two characteristics:
    - RX: for receiving data (from the hub's perspective)
    - TX: for transmitting data (from the hub's perspective)
    """
    _1 = "0000FD02"
    _2 = "1000-8000-00805F9B34FB"
    SERVICE = f"{_1}-0000-{_2}"
    RX = f"{_1}-0001-{_2}"
    TX = f"{_1}-0002-{_2}"

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