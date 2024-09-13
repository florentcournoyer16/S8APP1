from base_environment import BaseEnvironment, DutConfig
from base_uart_agent import RegAddr, UartConfig, UartTxCmd, UartRxPckt, TDCChannel, UartRxType
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
        self.trigger_agent = BaseTriggerAgent(dut.sipms)

    async def _test(self) -> None:
        response_ch0: UartRxPckt = await self._uart_agent.transaction(
            cmd=UartTxCmd.WRITE,
            addr=RegAddr.CHANNEL_EN_BITS,
            data=0x00
        )
        assert response_ch0.type == UartRxType.ACK_WRITE
        response_ch1: UartRxPckt = await self._uart_agent.transaction(
            cmd=UartTxCmd.WRITE,
            addr=RegAddr.CHANNEL_EN_BITS,
            data=0x01
        )
        assert response_ch1.type == UartRxType.ACK_WRITE

        pkts: list[UartRxPckt] = await self._uart_agent.listen_tdc(TDCChannel.CHAN0)

        pulse0 = PulseConfig(width=400, delay=400)
        await self.trigger_agent.single_pulse(pulse0)

        self._log.info(pkts[0])
