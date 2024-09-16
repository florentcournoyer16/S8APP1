from base_environment import BaseEnvironment, DutConfig
from base_uart_agent import UartConfig, UartTxCmd, BaseUartAgent
from crc8.crc8_mmc import CRC8MMC
from crc8.crc8_uart_agent import CRC8UartAgent
from cocotb.handle import HierarchyObject
from base_model import BaseModel, RegAddr


class CRC8Environment(BaseEnvironment):
    def __init__(
        self, dut: HierarchyObject, dut_config: DutConfig, uart_config: UartConfig,
    ):
        super(CRC8Environment, self).__init__(
            dut=dut, test_name="CRC8Environment",
            dut_config=dut_config,
            uart_config=uart_config,
            logger_name=type(self).__qualname__
        )
        
    def _build_env(self) -> None:
        super(CRC8Environment, self)._build_env()
        self._mmc_list.append(CRC8MMC(
            model=BaseModel(),
            logicblock_instance=self._dut.inst_packet_merger.inst_crc_calc
        ))

    def _set_uart_agent(self, uart_config: UartConfig) -> BaseUartAgent:
        return CRC8UartAgent(uart_config)

    async def _test(self) -> None:
        await self._test_crc8_valid()
        # await self._test_crc8_invalid()

    async def _test_crc8_valid(self) -> None:
        self._uart_agent.crc8_offset = 0
        await self._uart_agent.transaction(cmd=UartTxCmd.READ, addr=RegAddr.PRODUCT_VER_ID)
        await self._uart_agent.transaction(cmd=UartTxCmd.READ, addr=RegAddr.PRODUCT_VER_ID)
        await self._uart_agent.transaction(cmd=UartTxCmd.READ, addr=RegAddr.TDC_THRESH)
        await self._uart_agent.transaction(cmd=UartTxCmd.READ, addr=RegAddr.EN_EVENT_COUNT_RATE)

    async def _test_crc8_invalid(self) -> None:
        self._uart_agent.crc8_offset = 1
        await self._uart_agent.transaction(cmd=UartTxCmd.READ, addr=RegAddr.PRODUCT_VER_ID)
