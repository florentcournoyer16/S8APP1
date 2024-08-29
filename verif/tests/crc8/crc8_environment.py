from base_environment import BaseEnvironment, DutConfig
from uart_agent import RegAddr
from crc8.mmc_crc8 import MMCCRC8
from cocotb.handle import HierarchyObject
from uart_agent import UartConfig
from logger import logger
from cocotb import test


class CRC8Environment(BaseEnvironment):
    def __init__(
        self, dut: HierarchyObject, dut_config: DutConfig, uart_config: UartConfig
    ):
        super(CRC8Environment, self).__init__(
            dut=dut, test_name="CRC8", dut_config=dut_config, uart_config=uart_config
        )
        self.mmc: MMCCRC8 = MMCCRC8(
            model=super(CRC8Environment, self).uart_agent.calculate_crc8,
            logicblock_instance=dut.inst_packet_merger.inst_crc_calc,
        )

    async def test(self):
        logger.info("youpi")
        self.mmc.start()
        await self.uart_agent.read(addr=RegAddr.PRODUCT_VER_ID)
        self.mmc.stop()
