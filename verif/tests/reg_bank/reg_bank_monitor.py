from typing import Dict
from base_monitor import BaseMonitor
from cocotb.triggers import RisingEdge, Event, First, ClockCycles
from cocotb.handle import SimHandleBase


class RegBankInputMonitor(BaseMonitor):
    def __init__(self, clk: SimHandleBase, read_enable: SimHandleBase, write_enable, datas: Dict[str, SimHandleBase]):
        super(RegBankInputMonitor, self).__init__(clk, read_enable, datas, logger_name=type(self).__qualname__)
        self.read_enable = read_enable
        self.write_enable = write_enable

    async def _run(self) -> None:
        while True:
            await First(RisingEdge(self.read_enable), RisingEdge(self.write_enable))
            
            if self.write_enable.binstr == self.read_enable.binstr:
                continue
     
            # store the samples, as formatted by the _sample method
            self.values.put_nowait(self._sample())

class RegBankOutputMonitor(BaseMonitor):
    def __init__(self, clk: SimHandleBase, read_enable: SimHandleBase, write_enable, datas: Dict[str, SimHandleBase]):
        super(RegBankOutputMonitor, self).__init__(clk, read_enable, datas, logger_name=type(self).__qualname__)
        self._read_enable = read_enable
        self._write_enable = write_enable
        self.read_event: Event = Event()
        self.write_event: Event = Event()

    async def _run(self) -> None:
        while True:
            await First(RisingEdge(self._read_enable), RisingEdge(self._write_enable))

            if self._write_enable.binstr == self._read_enable.binstr:
                continue

            await ClockCycles(self._clk, num_cycles=1, rising=True)

            # store the samples, as formatted by the _sample method
            self.values.put_nowait(self._sample())
