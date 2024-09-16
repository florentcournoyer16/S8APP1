# This file is public domain, it can be freely copied without restrictions.
# SPDX-License-Identifier: CC0-1.0

# adapted from https://github.com/cocotb/cocotb/blob/stable/1.9/examples/matrix_multiplier/tests/test_matrix_multiplier.py

from typing import Dict, Tuple

from cocotb.handle import SimHandleBase
from base_monitor import BaseMonitor
from base_mmc import BaseMMC
from tdc.tdc_monitor import TDCInputMonitor, TDCOutputMonitor
from base_model import BaseModel
from base_uart_agent import TDCChannel


class TDCMMC(BaseMMC):
    def __init__(self, model: BaseModel, logicblock_instance: SimHandleBase, channel: TDCChannel):
        self._channel: TDCChannel = channel
        self.error_pulse_width: int = 0
        self.error_timestamp: int = 0
        self.smp_count = 0
        super(TDCMMC, self).__init__(model=model, logicblock_instance=logicblock_instance, logger_name=type(self).__qualname__+'.CHAN'+str(self._channel.value))

    def _set_monitors(self) -> Tuple[BaseMonitor, BaseMonitor]:
        input_mon: BaseMonitor = TDCInputMonitor(
            clk=self._logicblock.clk,
            trigger=self._logicblock.i_trigger,
            reset=self._logicblock.reset,
            datas=dict(i_enable_channel=self._logicblock.i_enable_channel),
            channel=self._channel
        )
        output_mon: BaseMonitor = TDCOutputMonitor(
            clk=self._logicblock.clk,
            has_event=self._logicblock.o_hasEvent,
            reset=self._logicblock.reset,
            datas=dict(o_pulseWidth=self._logicblock.o_pulseWidth, o_timestamp=self._logicblock.o_timestamp),
            channel=self._channel
        )
        return input_mon, output_mon

    # Insert logic to decide when to check the model against the HDL result.
    # then compare output monitor result with model result
    # This example might not work every time.
    async def _checker(self) -> None:
        mon_samples: Dict[str, int] = {}
        self.smp_count = 0
        while True:
            model_samples: tuple[int, int] = await self._model.tdc(
                i_trig_rising=self._input_mon.i_trig_rising,
                i_trig_falling=self._input_mon.i_trig_falling
            )
            model_pulse_width = hex(int(model_samples[0]))
            model_timestamp = hex(int(model_samples[1]))
            #self._log.info("%i. model_samples: o_pulseWidth = %s, o_timestamp = %s", self.smp_count, model_pulse_width, model_timestamp)

            mon_samples = await self._output_mon.values.get()
            mon_pulse_width = hex(mon_samples["o_pulseWidth"])
            mon_timestamp = hex(mon_samples["o_timestamp"])
            
            try:
                self.smp_count+=1
                assert model_pulse_width == mon_pulse_width
            except AssertionError:
                self._log.error("%i. monitor_samples: o_pulseWidth = %s", self.smp_count, mon_pulse_width)
                self._log.error("%i. model_samples: o_pulseWidth = %s", self.smp_count, model_pulse_width)
                self.error_pulse_width += 1
            try:
                assert model_timestamp == mon_timestamp
            except AssertionError:
                self._log.error("%i. monitor_samples: o_timestamp = %s", self.smp_count, mon_timestamp)
                self._log.error("%i. model_samples: o_timestamp = %s", self.smp_count, model_timestamp)
                self.error_timestamp += 1

    async def reset(self) -> None:
        self.smp_count = 0
        self.error_pulse_width = 0
        self.error_timestamp = 0
