from base_monitor import BaseMonitor
from cocotb.triggers import Edge, RisingEdge, Event, ClockCycles
from cocotb.handle import SimHandleBase
from base_uart_agent import TDCChannel

from typing import Dict

class TDCInputMonitor(BaseMonitor):
    def __init__(self, clk: SimHandleBase, trigger: SimHandleBase, reset: SimHandleBase, datas: Dict[str, SimHandleBase], channel: TDCChannel):
        self._channel = channel
        super(TDCInputMonitor, self).__init__(clk, datas, logger_name=type(self).__qualname__+'.CHAN'+str(self._channel.value))
        self._reset = reset
        self._trigger = trigger
        self.i_trig_falling: Event = Event()
        self.i_trig_rising: Event = Event()
        self.i_trig_falling.clear()
        self.i_trig_rising.clear()

    async def _run(self) -> None:
        while True:
            # self._log.info("waiting on i_trigger edge")
            await Edge(self._trigger)
            # self._log.info("i_trigger edge detected")
            
            if self._reset.value.binstr == '0':
                if self.i_trig_rising.is_set():
                    # self._log.info("i_trigger falling")
                    self.i_trig_falling.set()
                    self.i_trig_rising.clear()
                else:
                    # self._log.info("i_trigger rising")
                    self.i_trig_rising.set()
                    self.i_trig_falling.clear()

class TDCOutputMonitor(BaseMonitor):
    def __init__(self, clk: SimHandleBase, has_event: SimHandleBase, datas: Dict[str, SimHandleBase], channel: TDCChannel, reset: SimHandleBase):
        self._channel = channel
        self._reset = reset
        self._has_event = has_event
        super(TDCOutputMonitor, self).__init__(clk, datas, logger_name=type(self).__qualname__+'.CHAN'+str(self._channel.value))

    async def _run(self) -> None:
        while True:
            await RisingEdge(self._has_event)
            
            await ClockCycles(self._clk, num_cycles=1, rising=True)
            
            # self._log.info("o_hasEvent detected")

            self.values.put_nowait(self._sample())
