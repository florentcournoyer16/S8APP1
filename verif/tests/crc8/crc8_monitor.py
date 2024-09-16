from base_monitor import BaseMonitor
from cocotb.triggers import RisingEdge
from cocotb.handle import SimHandleBase

from typing import Dict

class CRC8InputMonitor(BaseMonitor):
    def __init__(self, clk: SimHandleBase, valid: SimHandleBase, datas: Dict[str, SimHandleBase]):
        super(CRC8InputMonitor, self).__init__(clk, valid, datas, logger_name=type(self).__qualname__)

    async def _run(self) -> None:
        while True:
            await RisingEdge(self._clk)
            # this condition decides when to record the signal states
            if self._valid.value.binstr != "1":
                # skip whatever comes after, and start the while loop again
                continue
            # store the samples, as formatted by the _sample method
            self.values.put_nowait(self._sample())

class CRC8OutputMonitor(BaseMonitor):
    def __init__(self, clk: SimHandleBase, valid: SimHandleBase, datas: Dict[str, SimHandleBase]):
        super(CRC8OutputMonitor, self).__init__(clk, valid, datas, logger_name=type(self).__qualname__)

    async def _run(self) -> None:
        while True:
            await RisingEdge(self._valid)
            # this condition decides when to record the signal states
            if self._valid.value.binstr != "1":
                # skip whatever comes after, and start the while loop again
                continue
            # store the samples, as formatted by the _sample method
            self.values.put_nowait(self._sample())
