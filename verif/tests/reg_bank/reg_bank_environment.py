from typing import Tuple, List
from base_environment import BaseEnvironment, DutConfig
from base_uart_agent import RegAddr, UartConfig, UartTxCmd, BaseUartAgent, UartRxPckt
from reg_bank.reg_bank_mmc import RegBankMMC
from cocotb.handle import HierarchyObject
from base_model import BaseModel
from random import randint
from logging import Logger
from cocotb.log import SimLog
from crc8.crc8_mmc import CRC8MMC

class RegBankEnvironment(BaseEnvironment):
    def __init__(
        self, dut: HierarchyObject, dut_config: DutConfig, uart_config: UartConfig,
    ):
        super(RegBankEnvironment, self).__init__(
            dut=dut,
            dut_config=dut_config,
            uart_config=uart_config,
            logger_name=type(self).__qualname__
        )
        self.test_dict = {
            'SA.6' : self._test_SA_6,
            'SD.4' : self._test_SD_4,
            'SD.5' : self._test_SD_5
        }

    def _set_uart_agent(self, uart_config: UartConfig) -> BaseUartAgent:
        return BaseUartAgent(uart_config)
    
    def _build_env(self) -> None:
        super(RegBankEnvironment, self)._build_env()
        self._mmc_list.append(RegBankMMC(
            model=BaseModel(),
            logicblock_instance=self._dut.registers_dut
        ))
        self._mmc_list.append(CRC8MMC(
            model=BaseModel(),
            logicblock_instance=self._dut.inst_packet_merger.inst_crc_calc
        ))

    async def _test(self, names: List[str]) -> None:
        test_fail = 0
        test_count = 0
        for name in names:
            test_fail += await self.test_dict[name]()
            test_count += 1
            await self.reset()

        self._log.info("Ran %i tests with %i FAIL", test_count, test_fail)
        assert test_fail == 0

        # await self._test_read_prod_id()
        # await self._test_rwr_thresh()
        # await self._test_rwr_cnt_rate()

    async def _test_read_prod_id(self) -> int:
        response: UartRxPckt = await self._uart_agent.transaction(
            cmd=UartTxCmd.READ,
            addr=RegAddr.PRODUCT_VER_ID
        )
        assert response.data == hex(0xBADEFACE)
        return 0

    async def _test_rwr_thresh(self) -> int:
        response = await self._uart_agent.transaction(cmd=UartTxCmd.READ, addr=RegAddr.TDC_THRESH)
        assert response.data == hex(0x00000000)
        await self._uart_agent.transaction(cmd=UartTxCmd.WRITE, addr=RegAddr.TDC_THRESH, data=0xBEE)
        response = await self._uart_agent.transaction(cmd=UartTxCmd.READ, addr=RegAddr.TDC_THRESH)
        assert response.data == hex(0xBEE)
        return 0

    async def _test_rwr_cnt_rate(self) -> int:
        current_val = await self._uart_agent.transaction(cmd=UartTxCmd.READ, addr=RegAddr.EN_COUNT_RATE)
        assert current_val.data in [hex(0x0), hex(0x1)]
        if current_val.data == hex(0x0):
            future_val = 1
        elif current_val.data == hex(0x1):
            future_val = 0
        await self._uart_agent.transaction(cmd=UartTxCmd.WRITE, addr=RegAddr.EN_COUNT_RATE, data=future_val)
        final_response = await self._uart_agent.transaction(cmd=UartTxCmd.READ, addr=RegAddr.EN_COUNT_RATE)
        assert final_response.data == hex(future_val)
        return 0
    
    async def _test_SA_6(self) -> None:
        test_name = "test_SA_6"
        test_log = SimLog("cocotb.%s" % test_name)
        test_log.info("Starting %s" % test_name)
        
        values: List[Tuple[RegAddr, int]] = [
            (RegAddr.PRODUCT_VER_ID, randint(0, 2**32)),
            (RegAddr.TDC_THRESH, randint(0, 2**32)),
            (RegAddr.DATA_MODE, randint(0, 2**32)),
            (RegAddr.BIAS_MODE, randint(0, 2**32)),
            (RegAddr.EN_COUNT_RATE, randint(0, 2**32)),
            (RegAddr.EN_EVENT_COUNT_RATE, randint(0, 2**32)),
            (RegAddr.SRC_SEL, randint(0, 2**32)),
            (RegAddr.SYNC_FLAG_ERR, randint(0, 2**32)),
            (RegAddr.CLEAR_SYNC_FLAG, randint(0, 2**32)),
            (RegAddr.CHANNEL_EN_BITS, randint(0, 2**32)),
        ]

        for value in values:
            await self._uart_agent.transaction(cmd=UartTxCmd.READ, addr=value[0], data=value[1])
            await self._uart_agent.transaction(cmd=UartTxCmd.WRITE, addr=value[0], data=value[1])
            await self._uart_agent.transaction(cmd=UartTxCmd.READ, addr=value[0], data=value[1])
        
        
        test_log.info("Finished %s" % test_name)
        return self.error_handling(test_log)


    async def _test_SD_4(self) -> int:
        test_name = "test_SD_4"
        test_log = SimLog("cocotb.%s" % test_name)
        test_log.info("Starting %s" % test_name)

        reg_list: List[RegAddr] = [
            RegAddr.DATA_MODE,
            RegAddr.BIAS_MODE,
            RegAddr.EN_COUNT_RATE,
            RegAddr.EN_EVENT_COUNT_RATE,
            RegAddr.TDC_THRESH,
            RegAddr.SRC_SEL,
            RegAddr.SYNC_FLAG_ERR,
            RegAddr.CLEAR_SYNC_FLAG,
            RegAddr.CHANNEL_EN_BITS,
            RegAddr.PRODUCT_VER_ID
        ]

        for reg in reg_list:
            await self._uart_agent.transaction(cmd=UartTxCmd.READ, addr=reg)

        values: List[Tuple[RegAddr, int]] = [
            (RegAddr.TDC_THRESH, 0xFFFFFFFF),
            (RegAddr.DATA_MODE, 11),
            (RegAddr.BIAS_MODE, 11),
            (RegAddr.EN_COUNT_RATE, 1),
            (RegAddr.EN_EVENT_COUNT_RATE, 1),
            (RegAddr.SRC_SEL, 1),
            (RegAddr.CLEAR_SYNC_FLAG, 1),
            (RegAddr.CHANNEL_EN_BITS, 0xFFFF)
        ]

        for value in values:
            await self._uart_agent.transaction(cmd=UartTxCmd.WRITE, addr=value[0], data=value[1])
            await self._uart_agent.transaction(cmd=UartTxCmd.READ, addr=value[0], data=value[1])
        
        test_log.info("Finished %s" % test_name)
        return self.error_handling(test_log)
    
    async def _test_SD_5(self) -> int:
        test_name = "test_SD_5"
        test_log = SimLog("cocotb.%s" % test_name)
        test_log.info("Starting %s" % test_name)

        values: List[Tuple[RegAddr, int]] = [
            (RegAddr.PRODUCT_VER_ID, 0xFFFFFFFF),
            (RegAddr.DATA_MODE, 0xFFFFFFFF),
            (RegAddr.BIAS_MODE, 0xFFFFFFFF),
            (RegAddr.EN_COUNT_RATE, 0xFFFFFFFF),
            (RegAddr.EN_EVENT_COUNT_RATE, 0xFFFFFFFF),
            (RegAddr.SRC_SEL, 0xFFFFFFFF),
            (RegAddr.CLEAR_SYNC_FLAG, 0xFFFFFFFF),
            (RegAddr.SYNC_FLAG_ERR, 0xFFFFFFFF),
            (RegAddr.CHANNEL_EN_BITS, 0xFFFFFFFF),
        ]

        for value in values:
            await self._uart_agent.transaction(cmd=UartTxCmd.READ, addr=value[0], data=value[1])
            await self._uart_agent.transaction(cmd=UartTxCmd.WRITE, addr=value[0], data=value[1])
            await self._uart_agent.transaction(cmd=UartTxCmd.READ, addr=value[0], data=value[1])
        
        test_log.info("Finished %s" % test_name)
        return self.error_handling(test_log)

    def error_handling(self, logger: Logger) -> int:
        if(self._mmc_list[0].error_count):
            logger.error("MMC FAIL : %i wrong values for readData or ackWrite", self._mmc_list[0].error_count)
            return 1
        return 0
    
