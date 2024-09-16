from cocotb import test
from crc8.crc8_environment import CRC8Environment
from base_environment import DutConfig
from base_uart_agent import UartConfig


@test()
async def tests_crc8_SD_3(dut):
    dut_config = DutConfig()
    uart_config = UartConfig()
    tests = []
    tests.append(CRC8Environment(dut, dut_config, uart_config))
    for test in tests:
        await test.run(names=['SD_3'])
