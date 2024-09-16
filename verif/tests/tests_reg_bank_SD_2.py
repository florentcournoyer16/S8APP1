from cocotb import test
from reg_bank.reg_bank_environment import RegBankEnvironment
from base_environment import DutConfig
from base_uart_agent import UartConfig


@test()
async def tests_reg_bank_SD_2(dut):
    dut_config = DutConfig()
    uart_config = UartConfig()
    tests = []
    tests.append(RegBankEnvironment(dut, dut_config, uart_config))
    for test in tests:
        await test.run(name="SD.2")
