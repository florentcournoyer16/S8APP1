from cocotb import test
from tdc.tdc_environment import TDCEnvironment
from base_environment import DutConfig
from base_uart_agent import UartConfig


@test()
async def tests_tdc_SA2(dut):
    dut_config = DutConfig()
    uart_config = UartConfig()
    tests = []
    tests.append(TDCEnvironment(dut, dut_config, uart_config))
    for test in tests:
        await test.run(names=['SA2'])
