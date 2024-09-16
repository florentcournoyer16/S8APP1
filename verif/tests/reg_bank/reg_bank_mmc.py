# This file is public domain, it can be freely copied without restrictions.
# SPDX-License-Identifier: CC0-1.0

# adapted from https://github.com/cocotb/cocotb/blob/stable/1.9/examples/matrix_multiplier/tests/test_matrix_multiplier.py

from typing import Dict, List, Tuple
from cocotb.handle import SimHandleBase
from reg_bank.reg_bank_monitor import RegBankOutputMonitor, RegBankInputMonitor
from base_mmc import BaseMMC
from base_monitor import BaseMonitor
from base_model import BaseModel

class RegBankMMC(BaseMMC):
    """
    Reusable checker of a checker instance

    Args
        logicblock_instance: handle to an instance of a logic block
    """

    def __init__(self, model: BaseModel, logicblock_instance: SimHandleBase):
        super(RegBankMMC, self).__init__(model=model, logicblock_instance=logicblock_instance, logger_name=type(self).__qualname__)

    def _set_monitors(self) -> Tuple[BaseMonitor, BaseMonitor]:
        input_mon: BaseMonitor = RegBankInputMonitor(
            clk=self._logicblock.clk,
            read_enable=self._logicblock.i_readEnable,
            write_enable=self._logicblock.i_writeEnable,
            datas=dict(
                i_writeEnable=self._logicblock.i_readEnable,
                i_readEnable=self._logicblock.i_writeEnable,
                i_address=self._logicblock.i_address,
                i_writeData=self._logicblock.i_writeData
            )
        )
        output_mon: BaseMonitor = RegBankOutputMonitor(
            clk=self._logicblock.clk,
            read_enable=self._logicblock.i_readEnable,
            write_enable=self._logicblock.i_writeEnable,
            datas=dict(
                o_writeAck=self._logicblock.o_writeAck,
                o_readData=self._logicblock.o_readData)
        )
        return input_mon, output_mon

    # Insert logic to decide when to check the model against the HDL result.
    # then compare output monitor result with model result
    # This example might not work every time.
    async def _checker(self) -> None:
        while True:
            # # dummy await, allows to run without checker implementation and verify monitors
            # await ClockCycles(self._logicblock.clk, 1000, rising=True)

            in_mon_samples: Dict[str, int] = {}
            
            in_mon_samples = await self._input_mon.values.get()
            
            i_write_enable = in_mon_samples["i_writeEnable"]
            i_read_enable = in_mon_samples["i_readEnable"]
            i_address = in_mon_samples["i_address"]
            i_write_data = in_mon_samples["i_writeData"]
            
            o_model: Tuple[int, int] = self._model.register_bank(
                write_enable=i_write_enable,
                read_enable=i_read_enable,
                address=i_address,
                write_data=i_write_data
            )
            o_write_ack_model = o_model[0]
            o_read_data_model = o_model[1]

            out_mon_samples = await self._output_mon.values.get()
            
            o_write_ack_mon = out_mon_samples["o_writeAck"]
            o_read_data_mon = out_mon_samples["o_readData"]

            self._log.info("o_write_ack_mon = %s, o_read_data_mon = %s", o_write_ack_mon, o_read_data_mon)
            self._log.info("o_write_ack_model = %s, o_read_data_model = %s", o_write_ack_model, o_read_data_model)

            assert (o_write_ack_model == o_write_ack_mon)
            assert (o_read_data_model == o_read_data_model)
