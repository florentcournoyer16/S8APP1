from cocotb.handle import HierarchyObject
from base_environment import BaseEnvironment, DutConfig
from base_uart_agent import RegAddr, UartConfig, UartTxCmd, UartRxPckt, UartRxType
from base_trigger_agent import BaseTriggerAgent, PulseConfig, TDCChannel
from tdc.tdc_mmc import TDCMMC
from base_model import BaseModel
from cocotb.triggers import ClockCycles

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
    
    def _build_env(self) -> None:
        super(TDCEnvironment, self)._build_env()
        self._mmc_list.append(TDCMMC(
            model=BaseModel(),
            logicblock_instance=self._dut.inst_tdc_channel_0,
            channel=TDCChannel.CHAN0
        ))
        self._mmc_list.append(TDCMMC(
            model=BaseModel(),
            logicblock_instance=self._dut.inst_tdc_channel_1,
            channel=TDCChannel.CHAN1
        ))

    async def _test(self) -> None:
        response_ch0: UartRxPckt = await self._uart_agent.transaction(
            cmd=UartTxCmd.WRITE,
            addr=RegAddr.CHANNEL_EN_BITS,
            data=0b01
        )
        assert response_ch0.type == UartRxType.ACK_WRITE
        for _ in range(5):

            await ClockCycles(self._dut.clk, num_cycles=1, rising=True)

            pulse0 = PulseConfig(rise_time=50, fall_time=100, channel=TDCChannel.CHAN0)
            await self.trigger_agent.send_pulses([pulse0])

            pkts: list[UartRxPckt] = await self._uart_agent.tdc_transaction(num_events=2)
            
