import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Join
from cocotbext.uart import UartSource, UartSink
import utilsVerif as uv
from cocotb.log import SimLog

import os

import pydevd_pycharm


async def _init_dut(dut):
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

# Decorator to tell cocotb this function is a coroutine
@cocotb.test()
async def cocotbext_uart(dut):
    print("Uart instance")

    # L2.E1 - Ajouter l'instanciation du MMC
    # inst_MMC_CRC8 = MMC_CRC8(dut.CheminVersPacketMergerCRC8)
    # await inst_MMC_CRC8.start()

    # L1.E4 - Ajouter l'initialisation des pattes d'entrée et de l'horloge
    await _init_dut(dut)

    # Driver and Sink for the dut UART RX/TX channels
    uart_driver = UartSource(dut.in_sig, baud=1000000, bits=8)
    uart_sink   = UartSink(dut.out_sig, baud=1000000, bits=8)

    # L1.E4 - Start thread for the reply function for the expected UART response.
    Task_returnMessage = await cocotb.start(wait_and_check_lab1(dut, uart_sink))

    # Generate arbitrary value to send on the UART
    #SomeValue = cocotb.binary.BinaryValue(value=0x1023456789ABDCEF, n_bits=64, bigEndian=False)

    SomeValue = uv.build_command_message(command=0x0, addr=0x09, data=0x0)

    # Print cocotb value demo function. Uncomment if desired.
    # print_cocotb_BinaryValue(SomeValue)

    # Send arbitrary value, then wait for transaction to complete
    await uart_driver.write(SomeValue.buff)
    await uart_driver.wait()

    # Calculate its CRC
    resultingCRC = uv.get_expected_crc(SomeValue.buff)
    # Convert to cocotb format
    crc_to_send = cocotb.binary.BinaryValue(value=resultingCRC, n_bits=8, bigEndian=False)
    # write to UART driver
    await uart_driver.write(crc_to_send.buff)

    # L1.E4 ait for response to complete or for timeout
    await Task_returnMessage



async def wait_and_check_lab1(dut, uart_sink):
    for x in range(0, 100):
        if(uart_sink.count() >= 7): ## 6 octets du message + le CRC
            break;
        await cocotb.triggers.ClockCycles(dut.clk, 1000, rising=True)
        logger = SimLog("cocotb.Test")

    if x == 99:
        print("Timeout")
        logger.info("Timeout for wait reply")
        raise RuntimeError("Timeout for wait reply")
        # or use plain assert.
        # assert False, "Timeout for wait reply"
        return None

    else:
        # cocotbext-uart returns byteArray. Convert to bytes first, then to Binary value for uniformity.
        message_bytes = bytes(await uart_sink.read(count=6))
        message = cocotb.binary.BinaryValue(value=message_bytes, n_bits=48, bigEndian=False)
        print("After a wait of " + str(x) + "000 clocks, received message: ", end='')
        print("0x{0:0{width}x}".format(message.integer, width=12))
        if message.integer != 0x0800badeface:
            logger.info(f"ERROR : 0x{message.integer: 12} != {0x0800badeface: 12}")
            raise RuntimeError("Bad message")
        else:
            logger.info(f"SUCCESS : 0x{message.integer: 12}")

# L.E4 function to wait for response message
async def wait_reply(dut, uart_sink):

    # Non-infinite wait loop. Throw cocotb exception if timeout is reached (to do)
    for x in range(0, 100):
        if(uart_sink.count() >= 7): ## 6 octets du message + le CRC
            break;
        await cocotb.triggers.ClockCycles(dut.clk, 1000, rising=True)

    if(x == 99):
        print("Timeout")
        logger = SimLog("cocotb.Test")
        logger.info("Timeout for wait reply")
        raise RuntimeError("Timeout for wait reply")
        # or use plain assert.
        #assert False, "Timeout for wait reply"
        return None

    else:
        # cocotbext-uart returns byteArray. Convert to bytes first, then to Binary value for uniformity.
        message_bytes = bytes(await uart_sink.read(count=6))
        message = cocotb.binary.BinaryValue(value=message_bytes, n_bits=48, bigEndian=False)
        print("After a wait of " + str(x) + "000 clocks, received message: ", end='')
        print("0x{0:0{width}x}".format(message.integer, width=12))
        return message
