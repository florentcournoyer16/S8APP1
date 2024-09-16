from base_environment import BaseEnvironment, DutConfig
from base_uart_agent import RegAddr, UartConfig, UartTxCmd, BaseUartAgent
from crc8.crc8_mmc import CRC8MMC
from crc8.crc8_uart_agent import CRC8UartAgent
from cocotb.handle import HierarchyObject
from base_model import BaseModel


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
        self.test_dict = {'SD3' : self._test_crc8_SD3,
                          'SA5' : self._test_crc8_SA5}
        
    def _build_env(self) -> None:
        super(CRC8Environment, self)._build_env()
        self._mmc_list.append(CRC8MMC(
            model=BaseModel(),
            logicblock_instance=self._dut.inst_packet_merger.inst_crc_calc
        ))

    def _set_uart_agent(self, uart_config: UartConfig) -> BaseUartAgent:
        return CRC8UartAgent(uart_config)

    async def _test(self, names:list[str]) -> None:
        await self._test_crc8_valid()
        # await self._test_crc8_invalid()
        test_fail = 0
        test_count = 0
        for name in names :
            test_fail += await self.test_dict[name]()
            test_count += 1
            await self.reset()
        self._log.info("Ran %i tests with %i FAIL", test_count, test_fail)
        assert test_fail == 0

    async def _test_crc8_SA5(self) -> None:
        self._uart_agent.crc8_offset = 0
        await self._uart_agent.transaction(cmd=UartTxCmd.READ, addr=RegAddr.PRODUCT_VER_ID)
        await self._uart_agent.transaction(cmd=UartTxCmd.READ, addr=RegAddr.PRODUCT_VER_ID)
        await self._uart_agent.transaction(cmd=UartTxCmd.READ, addr=RegAddr.TDC_THRESH)
        await self._uart_agent.transaction(cmd=UartTxCmd.READ, addr=RegAddr.EN_EVENT_COUNT_RATE)

    async def _test_crc8_SD3(self) -> None:
        self._uart_agent.crc8_offset = 1
        await self._uart_agent.transaction(cmd=UartTxCmd.READ, addr=RegAddr.PRODUCT_VER_ID)
