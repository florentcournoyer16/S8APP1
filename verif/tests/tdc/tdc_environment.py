from base_environment import BaseEnvironment, DutConfig
from base_uart_agent import RegAddr, UartConfig, UartTxCmd, BaseUartAgent, UartRxPckt
from cocotb.handle import HierarchyObject

class TDCEnvironment(BaseEnvironment):
    def __init__(
        self, dut: HierarchyObject, dut_config: DutConfig, uart_config: UartConfig,
    ):
        super(TDCEnvironment, self).__init__(
            dut=dut,
            test_name="TDCEnvironment",
            dut_config=dut_config,
            uart_config=uart_config,
            logger_name=type(self).__qualname__
        )

    def _set_uart_agent(self, uart_config: UartConfig) -> BaseUartAgent:
        return BaseUartAgent(uart_config)

    async def _test(self) -> None:
        response: UartRxPckt = await self._uart_agent.transaction(
            cmd=UartTxCmd.WRITE,
            addr=RegAddr.CHANNEL_EN_BITS,
            data=0x01
        )
        self._log.info(response)
