from typing import Tuple, List
from base_environment import BaseEnvironment, DutConfig
from base_uart_agent import RegAddr, UartConfig, UartTxCmd, BaseUartAgent, UartRxPckt
from reg_bank.reg_bank_mmc import RegBankMMC
from cocotb.handle import HierarchyObject
from base_model import BaseModel
from random import randint, seed


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
        return BaseUartAgent(uart_config)
    
    def _build_env(self) -> None:
        super(RegBankEnvironment, self)._build_env()
        self._mmc_list.append(RegBankMMC(
            model=BaseModel(),
            logicblock_instance=self._dut.registers_dut
        ))

    async def _test(self, name:str) -> None:
        if (name == "SD.1"):
            await self._test_SD_1()
        if (name == "SA.1"):
            await self._test_SA_1()
        # await self._test_read_prod_id()
        # await self._test_rwr_thresh()
        # await self._test_rwr_cnt_rate()

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

    async def _test_rwr_cnt_rate(self) -> None:
        current_val = await self._uart_agent.transaction(cmd=UartTxCmd.READ, addr=RegAddr.EN_COUNT_RATE)
        assert current_val.data in [hex(0x0), hex(0x1)]
        if current_val.data == hex(0x0):
            future_val = 1
        elif current_val.data == hex(0x1):
            future_val = 0
        await self._uart_agent.transaction(cmd=UartTxCmd.WRITE, addr=RegAddr.EN_COUNT_RATE, data=future_val)
        final_response = await self._uart_agent.transaction(cmd=UartTxCmd.READ, addr=RegAddr.EN_COUNT_RATE)
        assert final_response.data == hex(future_val)
    
    async def _test_SA_1(self) -> None:
        values: List[Tuple[RegAddr, int]] = [
            (RegAddr.DATA_MODE, randint(0, 2**32)),
            (RegAddr.BIAS_MODE, randint(0, 2**32)),
            (RegAddr.EN_COUNT_RATE, randint(0, 2**32)),
            (RegAddr.EN_EVENT_COUNT_RATE, randint(0, 2**32)),
            (RegAddr.TDC_THRESH, randint(0, 2**32)),
            (RegAddr.SRC_SEL, randint(0, 2**32)),
            (RegAddr.SYNC_FLAG_ERR, randint(0, 2**32)),
            (RegAddr.CLEAR_SYNC_FLAG, randint(0, 2**32)),
            (RegAddr.CHANNEL_EN_BITS, randint(0, 2**32)),
            (RegAddr.PRODUCT_VER_ID, randint(0, 2**32))
        ]

        for value in values:
            await self._uart_agent.transaction(cmd=UartTxCmd.READ, addr=value[0], data=value[1])
            await self._uart_agent.transaction(cmd=UartTxCmd.WRITE, addr=value[0], data=value[1])
            await self._uart_agent.transaction(cmd=UartTxCmd.READ, addr=value[0], data=value[1])


    async def _test_SD_1(self) -> None:
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
            (RegAddr.DATA_MODE, 11),
            (RegAddr.BIAS_MODE, 11),
            (RegAddr.EN_COUNT_RATE, 1),
            (RegAddr.EN_EVENT_COUNT_RATE, 1),
            (RegAddr.TDC_THRESH, 0xFFFFFFFF),
            (RegAddr.SRC_SEL, randint(0, 2**32)),
            (RegAddr.SYNC_FLAG_ERR, randint(0, 2**32)),
            (RegAddr.CLEAR_SYNC_FLAG, 1),
            (RegAddr.CHANNEL_EN_BITS, randint(0, 2**32)),
            (RegAddr.PRODUCT_VER_ID, randint(0, 2**32)),
        ]

        for value in values:
            await self._uart_agent.transaction(cmd=UartTxCmd.READ, addr=value[0], data=value[1])
            await self._uart_agent.transaction(cmd=UartTxCmd.WRITE, addr=value[0], data=value[1])
            await self._uart_agent.transaction(cmd=UartTxCmd.READ, addr=value[0], data=value[1])
    