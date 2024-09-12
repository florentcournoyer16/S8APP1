from base_environment import BaseEnvironment, DutConfig
from base_uart_agent import RegAddr, UartConfig, UartTxCmd, BaseUartAgent, UartRxPckt
from cocotb.handle import HierarchyObject
from cocotb import start_soon

class RegBankEnvironment(BaseEnvironment):
    def __init__(
        self, dut: HierarchyObject, dut_config: DutConfig, uart_config: UartConfig,
    ):
        super(RegBankEnvironment, self).__init__(
            dut=dut,
            test_name="RegBankEnvironment",
            dut_config=dut_config,
            uart_config=uart_config,
            logger_name=type(self).__qualname__
        )

    def _set_uart_agent(self, uart_config: UartConfig) -> BaseUartAgent:
        uart = BaseUartAgent(uart_config)
        start_soon(uart.sink_uart())
        return uart

    async def _test(self) -> None:
        await self._test_read_prod_id()
        await self._test_rwr_thresh()

    async def _test_read_prod_id(self) -> None:
        response: UartRxPckt = await self._uart_agent.transaction(
            cmd=UartTxCmd.READ,
            addr=RegAddr.PRODUCT_VER_ID
        )
        assert response.data == hex(0xBADEFACE)

    async def _test_rwr_thresh(self) -> None:
        response = await self._uart_agent.transaction(cmd=UartTxCmd.READ, addr=RegAddr.TDC_THRESH)
        assert response.data == hex(0x00000000)
        await self._uart_agent.transaction(cmd=UartTxCmd.WRITE, addr=RegAddr.TDC_THRESH, data=0xBEE)
        response = await self._uart_agent.transaction(cmd=UartTxCmd.READ, addr=RegAddr.TDC_THRESH)
        assert response.data == hex(0xBEE)
