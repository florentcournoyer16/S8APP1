from base_environment import BaseEnvironment, DutConfig
from base_uart_agent import RegAddr, UartConfig, UartTxCmd, BaseUartAgent, UartRxPckt, TDCChannel
from cocotb.handle import HierarchyObject
from base_trigger_agent import BaseTriggerAgent, PulseConfig
from cocotb import start_soon

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
        dut.sipms.value = 0x00
        self.trigger_agent = BaseTriggerAgent(dut.sipms)

    def _set_uart_agent(self, uart_config: UartConfig) -> BaseUartAgent:
        uart = BaseUartAgent(uart_config)
        start_soon(uart.sink_uart())
        return uart

    async def _test(self) -> None:
        response: UartRxPckt = await self._uart_agent.transaction(
            cmd=UartTxCmd.WRITE,
            addr=RegAddr.CHANNEL_EN_BITS,
            data=0x00
        )
        response: UartRxPckt = await self._uart_agent.transaction(
            cmd=UartTxCmd.WRITE,
            addr=RegAddr.CHANNEL_EN_BITS,
            data=0x01
        )

        mypulse = PulseConfig(400, 400)
        await self.trigger_agent.single_pulse(mypulse)
        pkts: list[UartRxPckt] = await self._uart_agent.listen_tdc(TDCChannel.CHAN0)

        self._log.info(pkts[0])

    