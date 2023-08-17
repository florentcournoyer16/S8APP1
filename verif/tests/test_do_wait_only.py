import cocotb
from cocotb.clock import Clock

# Decorator to tell cocotb this function is a coroutine
@cocotb.test()
async def test_do_wait_only(dut):
    print("Starting test_do_wait_only")

    # set a signal to some value
    dut.reset.value = 1

    # fetch value from a signal in the dut
    fetch_value = dut.reset.value

    # Confirm type of read signal. Expected: cocotb.binary.BinaryValue
    print(type(fetch_value))

    # start a clock signal
    cocotb.fork(Clock(dut.clk, 75, units='ns').start())

    # wait for 1000 clock periods
    await cocotb.triggers.ClockCycles(dut.clk, 1000, rising=True)

