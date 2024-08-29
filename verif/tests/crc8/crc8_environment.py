from base_environment import BaseEnvironment, DutConfig
from crc8.mmc_crc8 import MMCCRC8
from cocotb.handle import HierarchyObject
from uart_agent import UartConfig
from cocotb import test


class CRC8Environment(BaseEnvironment):
    def __init__(
        self, dut: HierarchyObject, dut_config: DutConfig, uart_config: UartConfig
    ):
        super(CRC8Environment, self).__init__(
            dut=dut, test_name="CRC8", dut_config=dut_config, uart_config=uart_config
        )
        self.mmc: MMCCRC8 = MMCCRC8(
            model=super(CRC8Environment, self).uart_agent.model,
            logicblock_instance=dut.inst_packet_merger.inst_crc_calc,
        )

    async def test(self):
        self.logger.info("youpi")
