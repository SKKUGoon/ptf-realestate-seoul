from enum import Enum
from typing import Final

# Center point: Seoul city. Boundary: Whole Seoul
SEOUL_CITYHALL_LAT: Final = 37.56568179655075
SEOUL_CITYHALL_LON: Final = 126.97802575206804

# Center point: Gangnam Station. Boundary: GBD
GANGNAM_STN_LAT: Final = 37.49781140190337
GANGNAM_STN_LON: Final = 127.02748954296155


class BaseBoundary(Enum):
    LEFT = None
    RIGHT = None
    UP = None
    DOWN = None
    bdname = None

    @classmethod
    def create(cls,
               left: int,
               right: int,
               up: int,
               down: int,
               bdname: str):
        member_map = {
            'LEFT': left, 'RIGHT': right, 'UP': up, 'DOWN': down, 'bdname': bdname
        }
        return Enum('CustomBoundary', member_map)


# Preset boundaries
SeoulBoundary = BaseBoundary.create(20, 18, 13, 18, "Seoul")
GangnamStnBoundary = BaseBoundary.create(2, 4, 4, 3, "Gangnam")
