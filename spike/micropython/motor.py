from ..lib.enumeration import HubPort, MotorEndState, MotorDeviceType
from .hub import Hub


def _port_num(p):  # accept enum or 'A'..'F'
    """Convert port to string name or int value."""
    if isinstance(p, HubPort):
        return int(p.value)
    elif isinstance(p, str) and p in HubPort.__members__:
        return HubPort[p].value
    elif isinstance(p,int) and p in HubPort._value2member_map_:
        return p
    raise ValueError(f"Invalid port: {p}")

class Port:
    IMPORT = "from hub import port"

    A = f"{__qualname__}.A"
    B = f"{__qualname__}.B"
    C = f"{__qualname__}.C"
    D = f"{__qualname__}.D"
    E = f"{__qualname__}.E"
    F = f"{__qualname__}.F"

class Motor:
    def __init__(self, port: HubPort | str, type: MotorDeviceType):
        self.PACKAGE = self.__class__.__name__.lower()
        
        self.port = _port_num(port)
        self.type = type

        match self.type:
            case MotorDeviceType.SMALL:
                self.velocity_range: int = (-660, 660)
            case MotorDeviceType.MEDIUM:
                self.velocity_range: int = (-1100, 1100)
            case MotorDeviceType.LARGE:
                self.velocity_range: int = (-1050, 1050)

        self.acceleration_range: int = (1, 10_000) # deg/sec^2
        self.deceleration_range: int = (1, 10_000) # deg/sec^2

    def run_for_degrees(self, degrees: int, velocity: int):
        """run_for_degrees(port: int, degrees: int, velocity: int, *, stop: int = BRAKE, acceleration: int = 1000, deceleration: int = 1000) -> Awaitable"""
        min_speed, max_speed = self.velocity_range
        if not (min_speed <= velocity <= max_speed):
            raise ValueError(f"Speed must be between {min_speed} and {max_speed} for {self.type.name}")
        return f"""
import {self.PACKAGE}
{self.PACKAGE}.run_for_degrees({Port.E}, {degrees}, {velocity})
"""