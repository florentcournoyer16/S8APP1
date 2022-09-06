import cocotb
from cocotb.clock import Clock

# Decorator to tell cocotb this function is a coroutine
@cocotb.test()
async def test_do_wait_only(dut):
    print("Starting test_do_wait_only")

    cocotb.fork(Clock(dut.clk, 10, units='ns').start())
    await cocotb.triggers.ClockCycles(dut.clk, 1000, rising=True)

