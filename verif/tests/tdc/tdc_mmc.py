# This file is public domain, it can be freely copied without restrictions.
# SPDX-License-Identifier: CC0-1.0

# adapted from https://github.com/cocotb/cocotb/blob/stable/1.9/examples/matrix_multiplier/tests/test_matrix_multiplier.py

from typing import Dict, List

from cocotb.handle import SimHandleBase
from cocotb.triggers import ClockCycles
from base_mmc import BaseMMC
from base_monitor import BaseMonitor
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
        input_mon: BaseMonitor = BaseMonitor(
            clk=self._logicblock.clk,
            valid=self._logicblock.i_valid,
            datas=dict(i_data=self._logicblock.i_data, i_last=self._logicblock.i_last)
        )

        output_mon: BaseMonitor = BaseMonitor(
            clk=self._logicblock.clk,
            valid=self._logicblock.o_done,
            datas=dict(o_match=self._logicblock.o_match, reset=self._logicblock.reset)
        )
        return input_mon, output_mon

    # Insert logic to decide when to check the model against the HDL result.
    # then compare output monitor result with model result
    # This example might not work every time.
    async def _checker(self) -> None:
        while True:
            pass
