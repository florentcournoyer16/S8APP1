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
        self.error_count = 0

    def _set_monitors(self) -> Tuple[BaseMonitor, BaseMonitor]:
        input_mon: BaseMonitor = RegBankInputMonitor(
            clk=self._logicblock.clk,
            read_enable=self._logicblock.readEnable,
            write_enable=self._logicblock.writeEnable,
            datas=dict(
                writeEnable=self._logicblock.writeEnable,
                readEnable=self._logicblock.readEnable,
                address=self._logicblock.address,
                writeData=self._logicblock.writeData
            )
        )
        output_mon: BaseMonitor = RegBankOutputMonitor(
            clk=self._logicblock.clk,
            read_enable=self._logicblock.readEnable,
            write_ack=self._logicblock.writeAck,
            datas=dict(
                writeAck=self._logicblock.writeAck,
                readData=self._logicblock.readData)
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
            out_mon_samples: Dict[str, int] = {}
            
            in_mon_samples = await self._input_mon.values.get()
            
            write_enable: int = in_mon_samples["writeEnable"]
            read_enable: int = in_mon_samples["readEnable"]
            address: int = in_mon_samples["address"]
            write_data: int = in_mon_samples["writeData"]
            
            self._log.info(
                "write_enable = %s, read_enable = %s, address = %s, write_data = %s",
                hex(write_enable), hex(read_enable),
                hex(address), hex(write_data)
            )
            
            model_output: Tuple[int, int] = self._model.register_bank(
                write_enable=write_enable,
                read_enable=read_enable,
                address=address,
                write_data=write_data
            )
            # self._log.info("model_output = %s", model_output)
            write_ack_model = model_output[0]
            read_data_model = model_output[1]

            out_mon_samples = await self._output_mon.values.get()
            
            write_ack_mon: int = out_mon_samples["writeAck"]
            read_data_mon: int = out_mon_samples["readData"]

            self._log.info("write_ack_mon = %s, read_data_mon = %s", hex(write_ack_mon), hex(read_data_mon))
            self._log.info("write_ack_model = %s, read_data_model = %s", hex(write_ack_model), hex(read_data_model))

            if (hex(write_ack_model) != hex(write_ack_mon)):
                self.error_count += 1
            if (hex(read_data_model) != hex(read_data_mon)):
                self.error_count += 1
