from typing import List
from cocotb.handle import HierarchyObject
from base_environment import BaseEnvironment, DutConfig
from base_uart_agent import UartConfig, UartTxCmd, UartRxPckt, UartRxType
from base_trigger_agent import BaseTriggerAgent, PulseConfig, TDCChannel
from tdc.tdc_mmc import TDCMMC
from base_model import BaseModel, RegAddr
from cocotb.triggers import ClockCycles, Timer
from random import randint, seed
from cocotb import start, Coroutine, Task, start_soon
from cocotb.log import SimLog

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
        self.tdc_error_count = 0
        self.smp_count = 0
    
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

    async def _test(self, name: str) -> None:
        test_fail = 0
        test_count = 0
        if(name == 'SA1'):
            test_fail += await self._test_SA_1()
            test_count += 1
            await self.reset()
        if(name == 'SA2'):
            test_fail += await self._test_SA_2()
            test_count += 1
            await self.reset()
        if(name == 'SA3'):
            test_fail += await self._test_SA_3()
            test_count += 1
            await self.reset()
        if(name == 'SA4'):
            test_fail += await self._test_SA_4()
            test_count += 1
            await self.reset()
        if(name == 'SD1'):
            test_fail += await self._test_SD_1()
            test_count += 1
            await self.reset()
        if(name == 'SD2'):
            test_fail += await self._test_SD_2()
            test_count += 1
            await self.reset()
        self._log.info("Sent %i pulses and received %i wrong values", self.smp_count, self.tdc_error_count)
        self._log.info("Ran %i tests with %i FAIL", test_count, test_fail)
        assert test_fail == 0

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
            
    async def _test_SA_1(self) -> int:
        # Initialise this test logger
        test_name = "test_SA_1"
        test_log = SimLog("cocotb.%s" % test_name)
        test_log.info("Starting %s" % test_name)
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
        pkts: list[UartRxPckt] = await self._uart_agent.tdc_transaction(num_events=2)
        
        
        # 5. Assert that only the first pulse has been detected by the TDC
        test_log.info("Finished %s" % test_name)
        self.error_handling(test_log)
        if(len(pkts) > 1):
            test_log.info("FAIL : CHAN0 sent data while disabled")
            return 1
        else:
            test_log.info("SUCCESS")
            return 0
    
    async def _test_SA_2(self) -> int:
        # Initialise this test logger
        test_name = "test_SA_2"
        test_log = SimLog("cocotb.%s" % test_name)
        test_log.info("Starting %s" % test_name)

        pkts: list[UartRxPckt] = []

        # Enables the CH0
        response_ch0: UartRxPckt = await self._uart_agent.transaction(
            cmd=UartTxCmd.WRITE,
            addr=RegAddr.CHANNEL_EN_BITS,
            data=0b01
        )
        assert response_ch0.type == UartRxType.ACK_WRITE

        for _ in range(10):
            rand_delay = randint(50, 100)
            rand_width = randint(20, 5000) + rand_delay

            # Generation of a random pulse on CH0
            rand_pulse = PulseConfig(rise_time=rand_delay, fall_time=rand_width, channel=TDCChannel.CHAN0)

            # Sending the pulses on the trigger signal
            await self.trigger_agent.send_pulses([rand_pulse], units='ns')

            # Waiting for the DUT to transeive the TDC interpolation 
            pkts.append(await self._uart_agent.tdc_transaction(num_events=2))


        test_log.info("Finished %s" % test_name)
        self.error_handling(test_log)
        if(len(pkts) == 20):
            test_log.info("FAIL : CHAN0 saw the wrong number of pulses")
            return 1
        else:
            test_log.info("SUCCESS")
            return 0

    async def _test_SA_3(self) -> int:
        # Initialise this test logger
        test_name = "test_SA_3"
        test_log = SimLog("cocotb.%s" % test_name)
        test_log.info("Starting %s" % test_name)

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
        pkts: list[UartRxPckt] = await self._uart_agent.tdc_transaction(num_events=18)

        test_log.info("Finished %s" % test_name)
        self.error_handling(test_log)
        if(len(pkts) == 18):
            test_log.info("FAIL : CHAN0 sent data while disabled")
            return 1
        else:
            test_log.info("SUCCESS")
            return 0

    async def _test_SA_4(self) -> int:
        # Initialise this test logger
        test_name = "test_SA_4"
        test_log = SimLog("cocotb.%s" % test_name)
        test_log.info("Starting %s" % test_name)

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
        pkts: list[UartRxPckt] = await self._uart_agent.tdc_transaction(num_events=20)

        test_log.info("Finished %s" % test_name)
        self.error_handling(test_log)
        if(len(pkts) == 20):
            test_log.info("FAIL : CHAN0 sent data while disabled")
            return 1
        else:
            test_log.info("SUCCESS")
            return 0
            
    async def _test_SD_1(self) -> int:
        # Initialise this test logger
        test_name = "test_SD_1"
        test_log = SimLog("cocotb.%s" % test_name)
        test_log.info("Starting %s" % test_name)

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

        self._dut.sipms[0].value = 0

        test_log.info("Finished %s" % test_name)
        self.error_handling(test_log)
        if(len(pkts) == 2):
            test_log.info("FAIL : CHAN0 sent data while disabled")
            return 1
        else:
            test_log.info("SUCCESS")
            return 0
        
    async def _test_SD_2(self) -> int:
        # Initialise this test logger
        test_name = "test_SD_2"
        test_log = SimLog("cocotb.%s" % test_name)
        test_log.info("Starting %s" % test_name)

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

        test_log.info("Finished %s" % test_name)
        self.error_handling(test_log)
        if(self._uart_agent._tdc_queue.qsize() == 0):
            test_log.info("FAIL : CHAN0 sent data while disabled")
            return 1
        else:
            test_log.info("SUCCESS")
            return 0

    async def reset(self):
        self._dut.reset.value = 1
        Timer(100, units='ns')
        #await self.trigger_agent.reset()
        await self._uart_agent.reset()
        for mmc in self._mmc_list:
            await mmc.reset()
        self._dut.reset.value = 0

    def error_handling(self, logger):
        if(self._mmc_list[0].error_timestamp):
            logger.info("MMC FAIL : %i o_timestamp out of %i were wrong in CH0", self._mmc_list[0].error_timestamp, self._mmc_list[0].smp_count)
            self.tdc_error_count += self._mmc_list[0].error_timestamp
        if(self._mmc_list[0].error_pulse_width):
            logger.info("MMC FAIL : %i o_pulseWidth out of %i were wrong in CH0", self._mmc_list[0].error_pulse_width, self._mmc_list[0].smp_count)
            self.tdc_error_count += self._mmc_list[0].error_pulse_width
        if(self._mmc_list[1].error_timestamp):
            logger.info("MMC FAIL : %i o_timestamp out of %i were wrong in CH1", self._mmc_list[1].error_timestamp, self._mmc_list[0].smp_count)
            self.tdc_error_count += self._mmc_list[1].error_timestamp
        if(self._mmc_list[1].error_pulse_width):
            logger.info("MMC FAIL : %i o_pulseWidth out of %i were wrong in CH1", self._mmc_list[1].error_pulse_width, self._mmc_list[0].smp_count)
            self.tdc_error_count += self._mmc_list[1].error_pulse_width
        self.smp_count += self._mmc_list[0].smp_count
        self.smp_count += self._mmc_list[1].smp_count
