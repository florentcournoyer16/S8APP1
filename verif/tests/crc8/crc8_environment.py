from base_environments import BaseEnvironment
from mmc_crc8 import MMCCRC8
from cocotb import test


class CRC8Environment(BaseEnvironment):
    def __init__(
        self, dut: HierarchyObject, dut_config: DutConfig, uart_config: UartConfig
    ):
        super(CRC8Environment, self).__init__(
            dut=dut, test_name="CRC8", dut_config=dut_config, uart_config=uart_config
        )
        self.mmc: MMCCRC8 = MMCCRC8(
            logicblock_instance=dut.inst_packet_merge.inst_crc_calc
        )

    async def test(self):
        self.logger.info("youpi")
