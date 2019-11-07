"""
Access supported PM sensors from a single object
"""


from datetime import datetime
from enum import Enum
from typing import NamedTuple, Optional
from pms import logger
from . import sensors


class Sensor(Enum):
    """Supported PM sensors"""

    PMSx003 = sensors.PMSx003
    PMS3003 = sensors.PMS3003
    PMS5003S = sensors.PMS5003S
    PMS5003ST = sensors.PMS5003ST
    PMS5003T = sensors.PMS5003T
    SDS01x = sensors.SDS01x
    SDS198 = sensors.SDS198
    HPMA115S0 = sensors.HPMA115S0
    HPMA115C0 = sensors.HPMA115C0
    SPS30 = sensors.SPS30

    PMS1003 = PMS5003 = PMS7003 = PMSA003 = PMSx003
    G1, G3, G5, G7, G10 = PMS1003, PMS3003, PMS5003, PMS7003, PMSA003
    SDS011 = SDS018 = SDS021 = SDS01x

    @property
    def Message(self) -> sensors.Message:
        return self.value.Message

    @property
    def Data(self) -> sensors.ObsData:
        return self.value.ObsData

    @property
    def Commands(self) -> sensors.Commands:
        return self.value.commands

    @property
    def baud(self) -> int:
        return 115200 if self.name == "SPS30" else 9600

    def guess(self, buffer: bytes) -> "Sensor":
        """Guess sensor type from buffer contents
        
        Need to issue the correct commands for a given sensor.
        Otherwise, the sensor will not wake up...
        """
        if buffer[-8:] == b"\x42\x4D\x00\x04\xe1\x00\x01\x74":
            sensor = "PMSx003"
        elif buffer[-10:-4] == b"\xAA\xC5\x02\x01\x01\x00":
            # SDS01x/SDS198 use the same commands
            sensor = "SDS198" if self.name == "SDS198" else "SDS01x"
        elif buffer:
            sensor = "PMS3003"
        else:
            sensor = "PMSx003"
            logger.debug(f"Sensor returned empty buffer, assume {sensor} on sleep mode")
        logger.debug(f"Guess {sensor} from buffer contents")
        return self.__class__[sensor]

    @staticmethod
    def now() -> int:
        """current time as seconds since epoch"""
        return int(datetime.now().timestamp())

    def command(self, cmd: str) -> sensors.Cmd:
        """Serial command for sensor"""
        return getattr(self.Commands, cmd)

    def decode(self, buffer: bytes, *, time: Optional[int] = None) -> NamedTuple:
        """Exract observations from serial buffer"""
        if not time:
            time = self.now()

        data = self.Message.decode(buffer, self.Commands.passive_read)
        return self.Data(time, *data)  # type: ignore
