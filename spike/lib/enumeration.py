from enum import IntEnum, unique

__all__ = [
    "Color",
    "HubPort",
    "HubFace",
    "ProgramAction",
    "ResponseStatus",
    "MotorEndState",
    "MotorMoveDirection",
    "MotorDeviceType",
]

@unique
class Color(IntEnum):
    BLACK = 0x00
    MAGENTA = 0x01
    PURPLE = 0x02
    BLUE = 0x03
    AZURE = 0x04
    TURQUOISE = 0x05
    GREEN = 0x06
    YELLOW = 0x07
    ORANGE = 0x08
    RED = 0x09
    WHITE = 0x0A
    NONE = 0xFF

@unique
class HubPort(IntEnum):
    A = 0x00
    B = 0x01
    C = 0x02
    D = 0x03
    E = 0x04
    F = 0x05

@unique
class HubFace(IntEnum):
    TOP = 0x00
    FRONT = 0x01
    RIGHT = 0x02
    BOTTOM = 0x03
    BACK = 0x04
    LEFT = 0x05

@unique
class ProgramAction(IntEnum):
    START = 0x00
    STOP = 0x01

@unique
class ResponseStatus(IntEnum):
    ACKNOWLEDGED = 0x00
    NOT_ACKNOWLEDGED = 0x01

@unique
class MotorEndState(IntEnum):
    """
    Smart coast/brake: methods of stopping a motor that compensate for inaccuracies when following commands.
    """
    COAST = 0x00
    BRAKE = 0x01
    HOLD = 0x02
    CONTINUE = 0x03
    COAST_SMART = 0x04
    BRAKE_SMART = 0x05
    DEFAULT = 0xFF

@unique
class MotorMoveDirection(IntEnum):
    CLOCKWISE = 0x00
    COUNTERCLOCKWISE = 0x01
    SHORTEST_PATH = 0x02
    LONGEST_PATH = 0x03

@unique
class MotorDeviceType(IntEnum):
    MEDIUM = 0x30
    LARGE = 0x31
    SMALL = 0x41
