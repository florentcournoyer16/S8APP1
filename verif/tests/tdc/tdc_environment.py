from typing import List
from cocotb.handle import HierarchyObject
from base_environment import BaseEnvironment, DutConfig
from base_uart_agent import RegAddr, UartConfig, UartTxCmd, UartRxPckt, UartRxType
from base_trigger_agent import BaseTriggerAgent, PulseConfig, TDCChannel
from tdc.tdc_mmc import TDCMMC
from base_model import BaseModel
from cocotb.triggers import ClockCycles, Timer
from random import randint, seed
from cocotb import start, Coroutine, Task, start_soon

INTRPLT_DLY = 3000

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
        for _ in range(5):
            #await self._test_init()
            #await self._test_SA_1()
            await self._test_SA_2()
            await self._test_SA_3()
            await self._test_SA_4()
            await self._test_SD_1()
            await self._test_SD_2()

    async def _test_init(self) -> None:
        response_ch0: UartRxPckt = await self._uart_agent.transaction(
            cmd=UartTxCmd.WRITE,
            addr=RegAddr.CHANNEL_EN_BITS,
            data=0b01
        )
        assert response_ch0.type == UartRxType.ACK_WRITE
        for _ in range(5):

            await ClockCycles(self._dut.clk, num_cycles=1, rising=True)

            pulse0 = PulseConfig(rise_time=50, fall_time=61, channel=TDCChannel.CHAN0)
            await self.trigger_agent.send_pulses([pulse0])

            pkts: list[UartRxPckt] = await self._uart_agent.tdc_transaction(num_events=2)
            
    async def _test_SA_1(self) -> None:
        # Enables the CH0
        response_ch0: UartRxPckt = await self._uart_agent.transaction(
            cmd=UartTxCmd.WRITE,
            addr=RegAddr.CHANNEL_EN_BITS,
            data=0b01
        )
        assert response_ch0.type == UartRxType.ACK_WRITE

        # 1. Generate a valid pulse
        timestamp = randint(20, 5000)
        rand_pulses = [PulseConfig(rise_time=50, fall_time=50 + timestamp, channel=TDCChannel.CHAN0)]
        
        # 2. Generate 20 random glitches (<20ns of pulse width)
        for i in range(20):
            timestamp += INTRPLT_DLY+50
            rand_glitch_width = randint(0, 19)
            rand_pulses.append(PulseConfig(rise_time=timestamp, fall_time=timestamp+rand_glitch_width, channel=TDCChannel.CHAN0))
            timestamp += rand_glitch_width

        # 3. Generate 20 other random cases from the first 20
        for i in range(10):
            timestamp += INTRPLT_DLY+50
            rand_glitch_width = randint(0, rand_pulses[i+1].fall_time-rand_pulses[i+1].rise_time)
            rand_pulses.append(PulseConfig(rise_time=timestamp, fall_time=timestamp+rand_glitch_width, channel=TDCChannel.CHAN0))
            timestamp += rand_glitch_width
            timestamp += INTRPLT_DLY+50
            rand_glitch_width = randint(rand_pulses[21-i].fall_time-rand_pulses[21-i].rise_time, 19)
            rand_pulses.append(PulseConfig(rise_time=timestamp, fall_time=timestamp+rand_glitch_width, channel=TDCChannel.CHAN0))
            timestamp += rand_glitch_width
        
        # 4. Send the geneated pulses
        start_soon(self.trigger_agent.send_pulses(rand_pulses, units='ns'))
        pkts: list[UartRxPckt] = await self._uart_agent.tdc_transaction(num_events=41)
        
        # 5. Assert that only the first pulse has been detected by the TDC
        assert len(pkts) == 1, "ERROR : TDC got triggered by a pulse less than 20ns"

        return
    
    async def _test_SA_2(self) -> None:
        pkts: list[UartRxPckt] = []

        # Enables the CH0
        response_ch0: UartRxPckt = await self._uart_agent.transaction(
            cmd=UartTxCmd.WRITE,
            addr=RegAddr.CHANNEL_EN_BITS,
            data=0b01
        )
        assert response_ch0.type == UartRxType.ACK_WRITE

        rand_pulses = []
        timestamp = 0
        for i in range(5):
            rand_delay = randint(50, 100)
            rand_width = randint(20, 5000) + rand_delay

            # Generation of a random pulse on CH0
            rand_pulses.append(PulseConfig(rise_time=timestamp+rand_delay, fall_time=timestamp+rand_width, channel=TDCChannel.CHAN0))
            timestamp+=rand_width+INTRPLT_DLY

        # Sending the pulses on the trigger signal
        start_soon(self.trigger_agent.send_pulses(rand_pulses, units='ns'))

        # Waiting for the DUT to transeive the TDC interpolation 
        pkts: list[UartRxPckt] = await self._uart_agent.tdc_transaction(num_events=10,retries=1000)

    async def _test_SA_3(self) -> None:
        pkts: list[UartRxPckt] = []

        # Enables the CH0
        response_ch0: UartRxPckt = await self._uart_agent.transaction(
            cmd=UartTxCmd.WRITE,
            addr=RegAddr.CHANNEL_EN_BITS,
            data=0b01
        )
        assert response_ch0.type == UartRxType.ACK_WRITE
        
        timestamp = 0
        rand_pulses = []
        for i in range(3):
            rand_rise = randint(50, 100)
            rand_fell = randint(21, 5000)+rand_rise
            rand_pulses.append(PulseConfig(rise_time=timestamp+rand_rise, fall_time=timestamp+rand_fell, channel=TDCChannel.CHAN0))
            timestamp += rand_fell + INTRPLT_DLY
            rand_pulses.append(PulseConfig(rise_time=timestamp+rand_rise, fall_time=timestamp+rand_fell+41, channel=TDCChannel.CHAN0))
            timestamp += rand_fell+41 + INTRPLT_DLY
            rand_pulses.append(PulseConfig(rise_time=timestamp+rand_rise, fall_time=timestamp+rand_fell-41, channel=TDCChannel.CHAN0))
            timestamp += rand_fell-41 + INTRPLT_DLY
        
        start_soon(self.trigger_agent.send_pulses(rand_pulses, units='ns'))
        pkts: list[UartRxPckt] = await self._uart_agent.tdc_transaction(num_events=18,retries=1000)

    async def _test_SA_4(self) -> None:
        pkts: list[UartRxPckt] = []

        # Enables the CH0
        response_ch0: UartRxPckt = await self._uart_agent.transaction(
            cmd=UartTxCmd.WRITE,
            addr=RegAddr.CHANNEL_EN_BITS,
            data=0b11
        )
        assert response_ch0.type == UartRxType.ACK_WRITE

        rand_pulses = []
        timestamp = 0
        for i in range(5):
            rand_delay = randint(50, 100)
            rand_width = randint(20, 5000) + rand_delay

            # Generation of a random pulse on CH0
            rand_pulses.append(PulseConfig(rise_time=timestamp+rand_delay, fall_time=timestamp+rand_width, channel=TDCChannel.CHAN0))
            timestamp+=rand_width+INTRPLT_DLY
        timestamp = 0
        for i in range(5):
            rand_delay = randint(50, 100)
            rand_width = randint(20, 5000) + rand_delay

            # Generation of a random pulse on CH0
            rand_pulses.append(PulseConfig(rise_time=timestamp+rand_delay, fall_time=timestamp+rand_width, channel=TDCChannel.CHAN1))
            timestamp+=rand_width+INTRPLT_DLY

        # Sending the pulses on the trigger signal
        start_soon(self.trigger_agent.send_pulses(rand_pulses, units='ns'))

        # Waiting for the DUT to transeive the TDC interpolation 
        pkts: list[UartRxPckt] = await self._uart_agent.tdc_transaction(num_events=20, retries=1000)

    async def _test_SD_1(self) -> None:
        # Enables the CH0
        response_ch0: UartRxPckt = await self._uart_agent.transaction(
            cmd=UartTxCmd.WRITE,
            addr=RegAddr.CHANNEL_EN_BITS,
            data=0b01
        )
        assert response_ch0.type == UartRxType.ACK_WRITE

        self._dut.sipms[0].value = 1

        Timer(20, units='us')

        pkts: list[UartRxPckt] = await self._uart_agent.tdc_transaction(num_events=3)

        assert len(pkts) == 2
        return
        
    async def _test_SD_2(self) -> None:
        response_ch0: UartRxPckt = await self._uart_agent.transaction(
            cmd=UartTxCmd.WRITE,
            addr=RegAddr.CHANNEL_EN_BITS,
            data=0b00
        )
        assert response_ch0.type == UartRxType.ACK_WRITE
        for i in range(5):

            await ClockCycles(self._dut.clk, num_cycles=201, rising=True)

            pulse0 = PulseConfig(rise_time=50, fall_time=100, channel=TDCChannel.CHAN0)
            await self.trigger_agent.send_pulses([pulse0])

        await ClockCycles(self._dut.clk, num_cycles=50000, rising=True)

        assert self._uart_agent._tdc_queue.qsize() == 0, "CHAN0 sent data while disabled"
        return
