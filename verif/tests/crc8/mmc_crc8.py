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

# dut.inst_packet_merge.inst_crc_calc.i_valid
# dut.inst_packet_merge.inst_crc_calc.i_last
# dut.inst_packet_merge.inst_crc_calc.i_data

# dut.inst_packet_merge.inst_crc_calc.o_crc8
# dut.inst_packet_merge.inst_crc_calc.o_done
# dut.inst_packet_merge.inst_crc_calc.o_match

# dut.inst_packet_merge.inst_crc_calc.r_crc8
# dut.inst_packet_merge.inst_crc_calc.r_done
# dut.inst_packet_merge.inst_crc_calc.r_match

# dut.inst_packet_merge.inst_crc_calc.reset
# dut.inst_packet_merge.inst_crc_calc.clk


class MMCCRC8:
    """
    Reusable checker of a checker instance

    Args
        logicblock_instance: handle to an instance of a logic block
    """

    def __init__(self, model: callable, logicblock_instance: SimHandleBase):
        self.dut = logicblock_instance
        self.log = SimLog("cocotb.MMC.%s" % (type(self).__qualname__))

        self.model: callable = model

        self.input_mon: Monitor = Monitor(
            clk=self.dut.clk,
            valid=self.dut.i_valid,
            datas=dict(idata=self.dut.i_data),
        )

        self.output_mon: Monitor = Monitor(
            clk=self.dut.clk,
            valid=self.dut.o_done,
            datas=dict(o_match=self.dut.o_match),
        )

        self._checkercoro: Optional[Task] = None

    def start(self) -> None:
        """Starts monitors, model, and checker coroutine"""
        if self._checkercoro is not None:
            raise RuntimeError("Monitor already started")
        self.input_mon.start()
        self.output_mon.start()
        self._checkercoro = start_soon(self._checker())

    def stop(self) -> None:
        """Stops everything"""
        if self._checkercoro is None:
            raise RuntimeError("Monitor never started")
        self.input_mon.stop()
        self.output_mon.stop()
        self._checkercoro.kill()
        self._checkercoro = None

    # # Model, modify as needed.
    # def model(self, echantillons) -> bool:
    #     # equivalent model to HDL code
    #     return False

    # Insert logic to decide when to check the model against the HDL result.
    # then compare output monitor result with model result
    # This example might not work every time.
    async def _checker(self) -> None:
        while True:
            # dummy await, allows to run without checker implementation and verify monitors
            await ClockCycles(self.dut.clk, 1000, rising=True)
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
