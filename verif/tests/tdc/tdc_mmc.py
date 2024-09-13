# This file is public domain, it can be freely copied without restrictions.
# SPDX-License-Identifier: CC0-1.0

# adapted from https://github.com/cocotb/cocotb/blob/stable/1.9/examples/matrix_multiplier/tests/test_matrix_multiplier.py

from typing import Dict, List

from cocotb.handle import SimHandleBase
from cocotb.triggers import ClockCycles
from base_monitor import BaseMonitor
from base_mmc import BaseMMC
from tdc.tdc_monitor import TDCInputMonitor, TDCOutputMonitor
from base_model import BaseModel

class TDCMMC(BaseMMC):
    """
    Reusable checker of a checker instance

    Args
        logicblock_instance: handle to an instance of a logic block
    """

    def __init__(self, model: BaseModel, logicblock_instance: SimHandleBase):
        super(TDCMMC, self).__init__(model=model, logicblock_instance=logicblock_instance, logger_name=type(self).__qualname__)

    def _set_monitors(self) -> tuple[BaseMonitor, BaseMonitor]:
        input_mon: BaseMonitor = TDCInputMonitor(
            clk=self._logicblock.clk,
            valid=self._logicblock.i_trigger,
            reset=self._logicblock.reset,
            datas=dict(i_enable_channel=self._logicblock.i_enable_channel)
        )

        output_mon: BaseMonitor = TDCOutputMonitor(
            clk=self._logicblock.clk,
            valid=self._logicblock.o_hasEvent,
            datas=dict(o_pulseWidth=self._logicblock.o_pulseWidth, o_timestamp=self._logicblock.o_timestamp)
        )
        return input_mon, output_mon

    # Insert logic to decide when to check the model against the HDL result.
    # then compare output monitor result with model result
    # This example might not work every time.
    async def _checker(self) -> None:
        mon_samples: Dict[str, int] = {}
        while True:

            model_samples = await self._model.tdc(
                i_trig_rising=self._input_mon.i_trig_rising,
                i_trig_falling=self._input_mon.i_trig_falling
            )

            self._log.info("model_samples: o_pulseWidth = %s, o_timestamp = %s", str(model_samples[0]), str(model_samples[1]))

            mon_samples = await self._output_mon.values.get()
    
            self._log.info("monitor_samples: o_pulseWidth = %s, o_timestamp = %s", hex(int(mon_samples["o_pulseWidth"])), hex(int(mon_samples["o_timestamp"])))
            
            assert (str(model_samples[0]), str(model_samples[1])) == (mon_samples["o_pulseWidth"], mon_samples["o_timestamp"])
