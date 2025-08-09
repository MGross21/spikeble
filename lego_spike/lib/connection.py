class UUID:
    """
    The LEGO SPIKE Prime Hub exposes a BLE GATT service with two characteristics:
    - RX: for receiving data (from the hub's perspective)
    - TX: for transmitting data (from the hub's perspective)
    """
    SERVICE = "0000FD02-0000-1000-8000-00805F9B34FB"
    RX = "0000FD02-0001-1000-8000-00805F9B34FB"
    TX = "0000FD02-0002-1000-8000-00805F9B34FB"