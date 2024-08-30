from base_environment import BaseEnvironment, DutConfig
from base_uart_agent import RegAddr, UartConfig, UartCmd, BaseUartAgent
from crc8.crc8_mmc import CRC8MMC
from cocotb.handle import HierarchyObject
from crc8.crc8_uart_agent import CRC8UartAgent


class CRC8Environment(BaseEnvironment):
    def __init__(
        self, dut: HierarchyObject, dut_config: DutConfig, uart_config: UartConfig,
    ):
        super(CRC8Environment, self).__init__(
            dut=dut, test_name="CRC8Environment", dut_config=dut_config, uart_config=uart_config, logger_name=type(self).__qualname__
        )
        
    def _build_env(self) -> None:
        super(CRC8Environment, self)._build_env()
        self._mmc.append(CRC8MMC(
            logicblock_instance=self._dut.inst_packet_merger.inst_crc_calc
        ))

    def _set_uart_agent(self, uart_config: BaseUartAgent) -> BaseUartAgent:
        return CRC8UartAgent(uart_config)

    async def _test(self):
        # await self.uart_agent.transaction(cmd=UartCmd.WRITE, addr=RegAddr.TDC_THRESH, data=0xCAFE)
        self.uart_agent.crc8_offset = 0
        await self.uart_agent.transaction(cmd=UartCmd.WRITE, addr=RegAddr.TDC_THRESH, data=0xCAFE)


