from cocotb import test
from tdc.tdc_environment import TDCEnvironment
from base_environment import DutConfig
from base_uart_agent import UartConfig
from cocotb import start, triggers 
from cocotb.clock import Clock
import os

import pydevd_pycharm


# Decorator to tell cocotb this function is a coroutine
@test()
async def tests_tdc(dut):
    print("Starting my_test")
    PYCHARMDEBUG = os.environ.get('PYCHARMDEBUG')

    print(PYCHARMDEBUG)

    if(PYCHARMDEBUG == "enabled"):
        pydevd_pycharm.settrace('localhost', port=9091, stdoutToServer=True, stderrToServer=True)

    # set a signal to some value
    dut.reset.value = 1

    # start a clock signal
    await start(Clock(dut.clk, 10, units='ns').start())

    # wait for 10 clock periods
    await triggers.ClockCycles(dut.clk, 100, rising=True)

    dut.reset.value = 0

    dut_config = DutConfig()
    uart_config = UartConfig()
    tests = []
    tests.append(TDCEnvironment(dut, dut_config, uart_config))
    for test in tests:
        await test.run()