from dataclasses import dataclass
from cocotb.handle import SimHandleBase

@dataclass
class PulseConfig:
    width : int = 0
    delay : int = 0


class BaseTriggerAgent():
    def init(self, trig : SimHandleBase):
        self._trig = trig

    def single_pulse(self, pulse : PulseConfig):
        