from dataclasses import dataclass
from cocotb.handle import ModifiableObject
from cocotb.triggers import Timer

@dataclass
class PulseConfig:
    width : int = 0
    delay : int = 0


class BaseTriggerAgent():
    def __init__(self, trig : ModifiableObject):
        self._trig = trig

    async def single_pulse(self, pulse : PulseConfig):
        await Timer(pulse.delay, units='ns')
        self._trig[0].value = 1
        await Timer(pulse.width, units='ns')
        self._trig[0].value = 0