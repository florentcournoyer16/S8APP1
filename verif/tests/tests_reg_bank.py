from cocotb import test
from reg_bank.reg_bank_environment import RegBankEnvironment
from base_environment import DutConfig
from base_uart_agent import UartConfig
import os

import pydevd_pycharm


# Decorator to tell cocotb this function is a coroutine
@test()
async def tests_reg_bank(dut):
    print("Starting my_test")
    PYCHARMDEBUG = os.environ.get('PYCHARMDEBUG')

    print(PYCHARMDEBUG)

    if(PYCHARMDEBUG == "enabled"):
        pydevd_pycharm.settrace('localhost', port=9091, stdoutToServer=True, stderrToServer=True)

    dut_config = DutConfig()
    uart_config = UartConfig()
    tests = []
    tests.append(RegBankEnvironment(dut, dut_config, uart_config))
    for test in tests:
        await test.run()
