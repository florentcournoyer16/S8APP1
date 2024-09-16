from base_environment import BaseEnvironment, DutConfig
from base_uart_agent import RegAddr, UartConfig, UartTxCmd, BaseUartAgent, UartRxPckt
from reg_bank.reg_bank_mmc import RegBankMMC
from cocotb.handle import HierarchyObject
from base_model import BaseModel


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
            logicblock_instance=self._dut.register_dut
        ))

    async def _test(self) -> None:
        await self._test_read_prod_id()
        await self._test_rwr_thresh()
        await self._test_rwr_cnt_rate()

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
