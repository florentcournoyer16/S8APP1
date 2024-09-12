# This file is public domain, it can be freely copied without restrictions.
# SPDX-License-Identifier: CC0-1.0

# adapted from https://github.com/cocotb/cocotb/blob/stable/1.9/examples/matrix_multiplier/tests/test_matrix_multiplier.py

from typing import Any, Dict, List, Optional

from cocotb import start_soon, Task
from cocotb.clock import Clock
from cocotb.handle import SimHandleBase
from cocotb.queue import Queue
from cocotb.triggers import RisingEdge, ClockCycles
from crc8.crc8_output_monitor import CRC8OutputMonitor
from base_mmc import BaseMMC
from utils_verif import calculateCRC8_singleCycle
from base_monitor import BaseMonitor
from base_model import BaseModel

class CRC8MMC(BaseMMC):
    """
    Reusable checker of a checker instance

    Args
        logicblock_instance: handle to an instance of a logic block
    """

    def __init__(self, model: BaseModel, logicblock_instance: SimHandleBase):
        super(CRC8MMC, self).__init__(model=model, logicblock_instance=logicblock_instance, logger_name=type(self).__qualname__)

    def _set_monitors(self) -> tuple[BaseMonitor, BaseMonitor]:
        input_mon: BaseMonitor = BaseMonitor(
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
            # dummy await, allows to run without checker implementation and verify monitors
            await ClockCycles(self._logicblock.clk, 1000, rising=True)

            mon_samples: List[Dict[str, int]] = []
            while True:
                mon_samples.append((await self._input_mon.values.get()))
                if mon_samples[len(mon_samples)-1]["i_last"] == 1:
                     break

            bytes_aray: bytes = bytes([sample['i_data'] for sample in mon_samples])

            o_match_model = self._model.crc8(bytes_aray)

            o_match_logicblock = await self._output_mon.values.get()

            self._log.info(f"o_match_logicblock = {o_match_logicblock}")

            assert (o_match_model == o_match_logicblock['o_match'])



            #while not self._input_mon.values.empty():
                #self._input_mon.values.get_nowait()

            #while not self._output_mon.values.empty():
                #continue

            """
            Récupérer toutes les valeurs dans une Queue:
            SamplesList = []
            while(not self.mon.values.empty()):
                SamplesList.append(self.mon.values.get_nowait())
            
            Prendre la valeur d'un signal, au nième élément seulement
            SamplesList[N]["NomDictionnaire"]
            
            Prendre la valeur d'un signal, au nième élément, et changer son type pour un entier
            SamplesList[N]["NomDictionnaire"].integer
                                        
            Extraire toutes les valeurs d'un signal d'une telle liste:
            SignalSamples = [d['NomSignal'] for d in SamplesList]
            --> depuis https://stackoverflow.com/questions/7271482/getting-a-list-of-values-from-a-list-of-dicts
            
            Même chose, mais en changeant aussi les valeur d'un bus pour des entiers
            ValueList = [d['NomSignal'].integer for d in expected_inputs]
            
            Lire une valeur dès que disponible, attendre sinon
            actual = await self.mon.values.get()

            # compare expected with actual using assertions. 
            assert actual["SignalC"] == expected
            """
