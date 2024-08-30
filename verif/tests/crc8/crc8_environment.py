from base_environment import BaseEnvironment, DutConfig
from uart_agent import RegAddr
from crc8.mmc_crc8 import MMCCRC8
from cocotb.handle import HierarchyObject
from uart_agent import UartConfig, UartCmd
from cocotb import test


class CRC8Environment(BaseEnvironment):
    def __init__(
        self, dut: HierarchyObject, dut_config: DutConfig, uart_config: UartConfig,
    ):
        super(CRC8Environment, self).__init__(
            dut=dut, test_name="CRC8", dut_config=dut_config, uart_config=uart_config, logger_name=type(self).__qualname__
        )
        
    def _build_env(self) -> None:
        super(CRC8Environment, self)._build_env()
        self._mmc.append(MMCCRC8(
            logicblock_instance=self._dut.inst_packet_merger.inst_crc_calc
        ))

    async def _test(self):
        await self.uart_agent.transaction(cmd=UartCmd.WRITE, addr=RegAddr.TDC_THRESH, data=0xCAFE)
        await self.uart_agent.transaction(cmd=UartCmd.READ, addr=RegAddr.TDC_THRESH)
