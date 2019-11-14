"""Data acquisition and logging tool for PM sensors with UART interface"""
__version__ = "0.1.5"


import logging, os

logging.basicConfig(level=os.getenv("LEVEL", "WARNING"))
logger = logging.getLogger(__name__)


class SensorWarning(UserWarning):
    """Recoverable errors"""

    pass


class WrongMessageFormat(SensorWarning):
    """Wrongly formattted message: throw away observation"""

    pass


class WrongMessageChecksum(SensorWarning):
    """Failed message checksum: throw away observation"""

    pass


class SensorWarmingUp(SensorWarning):
    """Empty message: throw away observation and wait until sensor warms up"""

    pass
