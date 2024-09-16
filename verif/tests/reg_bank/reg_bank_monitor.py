from typing import Dict
from base_monitor import BaseMonitor
from cocotb.triggers import RisingEdge, Event, First, ClockCycles
from cocotb.handle import SimHandleBase


class RegBankInputMonitor(BaseMonitor):
    def __init__(self, clk: SimHandleBase, read_enable: SimHandleBase, write_enable: SimHandleBase, datas: Dict[str, SimHandleBase]):
        super(RegBankInputMonitor, self).__init__(clk, read_enable, datas, logger_name=type(self).__qualname__)
        self.read_enable: SimHandleBase = read_enable
        self.write_enable: SimHandleBase = write_enable

    async def _run(self) -> None:
        while True:
            await First(RisingEdge(self.read_enable), RisingEdge(self.write_enable))
            
            if self.write_enable.value.binstr == self.read_enable.value.binstr:
                continue
     
            # store the samples, as formatted by the _sample method
            self.values.put_nowait(self._sample())

class RegBankOutputMonitor(BaseMonitor):
    def __init__(self, clk: SimHandleBase, read_enable: SimHandleBase, write_ack: SimHandleBase, datas: Dict[str, SimHandleBase]):
        super(RegBankOutputMonitor, self).__init__(clk, read_enable, datas, logger_name=type(self).__qualname__)
        self._read_enable = read_enable
        self._write_ack = write_ack
        self.read_event: Event = Event()
        self.write_event: Event = Event()

    async def _run(self) -> None:
        while True:
            await First(RisingEdge(self._read_enable), RisingEdge(self._write_ack))

            if self._write_ack.value.binstr == self._read_enable.value.binstr:
                continue
            
            if self._read_enable.value.binstr == '1':
                self._log.info("readEnable sampled")
                await ClockCycles(self._clk, num_cycles=3, rising=True)
            else:
                self._log.info("writeAck sampled")

            # store the samples, as formatted by the _sample method
            self.values.put_nowait(self._sample())
