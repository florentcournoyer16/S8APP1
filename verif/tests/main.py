import cocotb
from cocotb.clock import Clock
from crc8.crc8_environment import CRC8Environment
from base_environment import DutConfig
from uart_agent import UartConfig
from logger import LoggerSingleton
import os

import pydevd_pycharm


# Decorator to tell cocotb this function is a coroutine
@cocotb.test()
async def main(dut):
    print("Starting my_test")

    dut_config = DutConfig()
    uart_config = UartConfig()
    LoggerSingleton()
    tests = []
    tests.append(CRC8Environment(dut, dut_config, uart_config))
    for test in tests:
        await test.run()
