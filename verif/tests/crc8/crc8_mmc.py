# This file is public domain, it can be freely copied without restrictions.
# SPDX-License-Identifier: CC0-1.0

# adapted from https://github.com/cocotb/cocotb/blob/stable/1.9/examples/matrix_multiplier/tests/test_matrix_multiplier.py

from typing import Dict, List, Tuple
from cocotb.handle import SimHandleBase
from crc8.crc8_monitor import CRC8OutputMonitor, CRC8InputMonitor
from base_mmc import BaseMMC
from base_monitor import BaseMonitor
from base_model import BaseModel

class CRC8MMC(BaseMMC):

    def __init__(self, model: BaseModel, logicblock_instance: SimHandleBase):
        super(CRC8MMC, self).__init__(model=model, logicblock_instance=logicblock_instance, logger_name=type(self).__qualname__)
        self.crc8_error_count = 0

    def _set_monitors(self) -> Tuple[BaseMonitor, BaseMonitor]:
        input_mon: BaseMonitor = CRC8InputMonitor(
            clk=self._logicblock.clk,
            valid=self._logicblock.i_valid,
            datas=dict(i_data=self._logicblock.i_data, i_last=self._logicblock.i_last)
        )

        output_mon: BaseMonitor = CRC8OutputMonitor(
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
            # # dummy await, allows to run without checker implementation and verify monitors
            # await ClockCycles(self._logicblock.clk, 1000, rising=True)

            mon_samples: List[Dict[str, int]] = []
            while True:
                mon_samples.append((await self._input_mon.values.get()))
                if mon_samples[len(mon_samples)-1]["i_last"] == 1:
                     break

            bytes_aray: bytes = bytes([sample['i_data'] for sample in mon_samples])

            o_match_model = self._model.crc8(bytes_aray)

            o_match_logicblock = await self._output_mon.values.get()

            self._log.info("o_match_logicblock = %s", o_match_logicblock)
            
            if(o_match_model != o_match_logicblock['o_match']):
                self.crc8_error_count+=1

            #while not self._input_mon.values.empty():
                #self._input_mon.values.get_nowait()

            #while not self._output_mon.values.empty():
                #continue

    async def reset(self):
        self.crc8_error_count=0
