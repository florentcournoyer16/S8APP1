from base_monitor import BaseMonitor
from cocotb.triggers import Edge, RisingEdge
from cocotb.handle import SimHandleBase
from cocotb.triggers import Event, ClockCycles

from typing import Dict

class TDCInputMonitor(BaseMonitor):
    def __init__(self, clk: SimHandleBase, valid: SimHandleBase, reset: SimHandleBase, datas: Dict[str, SimHandleBase]):
        super(TDCInputMonitor, self).__init__(clk, valid, datas)
        self._reset = reset
        self.i_trig_falling: Event = Event()
        self.i_trig_rising: Event = Event()
        self.i_trig_falling.clear()
        self.i_trig_rising.clear()

    async def _run(self) -> None:
        while True:
            self._log.info("waiting on i_trigger edge")
            await Edge(self._valid)
            self._log.info("i_trigger edge detected")
            
            if self._reset.value.binstr == '0':
                if self.i_trig_rising.is_set():
                    self._log.info("i_trigger falling")
                    self.i_trig_falling.set()
                    self.i_trig_rising.clear()
                else:
                    self._log.info("i_trigger rising")
                    self.i_trig_rising.set()
                    self.i_trig_falling.clear()

class TDCOutputMonitor(BaseMonitor):
    async def _run(self) -> None:
        while True:
            await RisingEdge(self._valid)
            
            await ClockCycles(self._clk, num_cycles=1, rising=True)
            
            self._log.info("o_hasEvent detected")

            self.values.put_nowait(self._sample())
