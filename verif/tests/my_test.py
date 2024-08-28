import cocotb
from cocotb.clock import Clock

import os

import pydevd_pycharm


# Decorator to tell cocotb this function is a coroutine
@cocotb.test()
async def my_test(dut):
    print("Starting my_test")
    message = [0, 1, 0, 0, 0, 1, 1, 0, 0]
    PYCHARMDEBUG = os.environ.get('PYCHARMDEBUG')

    print(PYCHARMDEBUG)

    if(PYCHARMDEBUG == "enabled"):
        pydevd_pycharm.settrace('localhost', port=50100, stdoutToServer=True, stderrToServer=True)

    dut.reset.value = 1
    dut.in_sig.value = 0
    dut.resetCyclic.value = 0
    dut.sipms.integer = 0
    dut.clkMHz.value = 0
    # fetch value from a signal in the dut
    fetch_value = dut.reset.value

    # Confirm type of read signal. Expected: cocotb.binary.BinaryValue
    print(type(fetch_value))

    # start a clock signal
    await cocotb.start(Clock(dut.clk, 10, units='ns').start())

    # wait for 10 clock periods
    await cocotb.triggers.ClockCycles(dut.clk, 10, rising=True)

    dut.reset.value = 0

    await cocotb.triggers.ClockCycles(dut.clk, 10, rising=True)

    for i in range(0, 8):
        dut.in_sig.value = message[i]
        await cocotb.triggers.ClockCycles(dut.clk, 100, rising=True)
