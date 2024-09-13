from dataclasses import dataclass
from cocotb.handle import ModifiableObject
from cocotb.triggers import Timer

@dataclass
class PulseConfig:
    width: int
    delay: int
    units: str = "ns"

class BaseTriggerAgent():
    def __init__(self, trig: ModifiableObject):
        self._trig = trig
        self._trig[0].value = 0
        self._trig[1].value = 0

    async def single_pulse(self, pulse : PulseConfig):
        await Timer(pulse.delay, units=pulse.units)
        self._trig[0].value = 1
        await Timer(pulse.width, units=pulse.units)
        self._trig[0].value = 0
