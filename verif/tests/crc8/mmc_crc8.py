# This file is public domain, it can be freely copied without restrictions.
# SPDX-License-Identifier: CC0-1.0

# adapted from https://github.com/cocotb/cocotb/blob/stable/1.9/examples/matrix_multiplier/tests/test_matrix_multiplier.py

from typing import Any, Dict, List, Optional

from cocotb import start_soon, Task
from cocotb.clock import Clock
from cocotb.handle import SimHandleBase
from cocotb.queue import Queue
from cocotb.triggers import RisingEdge, ClockCycles
from cocotb.log import SimLog
from monitor import Monitor
from base_mmc import BaseMMC
from utils_verif import calculateCRC8_singleCycle

CRC8_START = 0x0D

class MMCCRC8(BaseMMC):
    """
    Reusable checker of a checker instance

    Args
        logicblock_instance: handle to an instance of a logic block
    """

    def __init__(self, logicblock_instance: SimHandleBase):
        super(MMCCRC8, self).__init__(logicblock_instance=logicblock_instance, logger_name=type(self).__qualname__)


    def _construct_monitors(self) -> tuple[Monitor, Monitor]:
        input_mon: Monitor = Monitor(
            clk=self._logicblock.clk,
            valid=self._logicblock.i_valid,
            datas=dict(i_data=self._logicblock.i_data)
        )

        output_mon: Monitor = Monitor(
            clk=self._logicblock.clk,
            valid=self._logicblock.o_done,
            datas=dict(o_match=self._logicblock.o_match)
        )
        return input_mon, output_mon

    # # Model, modify as needed.
    def model(self, echantillons) -> bool:
        # equivalent model to HDL code
        crc = echantillons[len(echantillons)-1]["i_data"]
        data = [d['i_data'].integer for d in echantillons][:len(echantillons)-1]

        current_crc = CRC8_START
        for current_byte in data:
            current_crc = calculateCRC8_singleCycle(current_byte, current_crc)
        return current_crc == crc

    # Insert logic to decide when to check the model against the HDL result.
    # then compare output monitor result with model result
    # This example might not work every time.
    async def _checker(self) -> None:
        while True:
            # dummy await, allows to run without checker implementation and verify monitors
            await ClockCycles(self._logicblock.clk, 1000, rising=True)

            SamplesList = []
            while len(SamplesList) <= 6:
                SamplesList.append((await self._input_mon.values.get()))

            match = self.model(SamplesList)

            assert match == (await self._output_mon.values.get())['o_match']

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


