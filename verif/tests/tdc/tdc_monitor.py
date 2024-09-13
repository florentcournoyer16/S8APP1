from base_monitor import BaseMonitor
from cocotb.triggers import Edge
from cocotb.handle import SimHandleBase

from typing import Dict
class TDCInputMonitor(BaseMonitor):
    def __init__(self, clk: SimHandleBase, valid: SimHandleBase, datas: Dict[str, SimHandleBase]):
        super(TDCInputMonitor, self).__init__(clk, valid, datas)

    async def _run(self) -> None:
        while True:
            await Edge(self._valid)
            # this condition decides when to record the signal states

            # store the samples, as formatted by the _sample method
            self.values.put_nowait(self._sample())
