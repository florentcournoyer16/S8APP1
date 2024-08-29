import cocotb
from cocotb.clock import Clock
from crc8_environment import CRC8Environment
import os

import pydevd_pycharm


# Decorator to tell cocotb this function is a coroutine
@cocotb.test()
async def main(dut):
    print("Starting my_test")

    dut_config = DutConfig()
    uart_config = UartConfig()

    tests = []
    tests.append(CRC8Environment(dut_config, uart_config))
    for test in tests:
        test.run(dut)
