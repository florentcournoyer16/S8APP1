import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Join
from cocotbext.uart import UartSource, UartSink
from gel815utils import gei815_print_cocotb_BinaryValue


# Decorator to tell cocotb this function is a coroutine
@cocotb.test()
async def test_cocotbext_uart_demo(dut):
    print("Uart instance demo")

    # L.E5 - Ajouter l'instanciation du moniteur
    # inst_Uart8Monitor = Monitor_VotreNomDeClasse(dut.CheminVersPacketMerger, logging=True)
    # inst_Uart8Monitor.name = "inst_Uart8Monitor" # optionnel

    # L.E6 - Ajout des moniteurs, modèles et scoreboard
    # VerifStuff = TestbenchClass_WithOnlyScoreboard(dut, logging=True)
    # VerifStuff.BuildVerificationComponents()

    # L.E4 - Ajouter l'initialisation des pattes d'entrée et de l'horloge
    # await votre_initialisation(dut) 

    # Driver and Sink for the dut UART RX/TX channels
    uart_driver = UartSource(dut.in_sig, baud=1000000, bits=8)
    uart_sink   = UartSink(dut.out_sig, baud=1000000, bits=8)

    # L.E4 - Start thread for the monitoring function (not monitor class) for the expected UART response.
    # Task_returnMessage =  cocotb.start_soon(wait_reply(dut, uart_sink))

    # Generate arbitrary value to send on the UART
    SomeValue = cocotb.binary.BinaryValue(value=0x1023456789ABDCEF, n_bits=64, bigEndian=False)

    # Print cocotb value demo function. Uncomment if desired.
    # gei815_print_cocotb_BinaryValue(SomeValue)

    # Send arbitrary value, then wait for transaction to complete
    await uart_driver.write(SomeValue.buff)
    await uart_driver.wait()

    # L.E4 ait for response to complete or for timeout
    # await Join(Task_returnMessage)


# L.E4 function to wait for response message
async def wait_reply(dut, uart_sink):

    # Non-infinite wait loop. Throw cocotb exception if timeout is reached (to do)
    for x in range(0, 100):
        if(uart_sink.count() >= 6):
            break;
        await cocotb.triggers.ClockCycles(dut.clk, 1000, rising=True)

    if(x == 100):
        print("Timeout")
        # todo: Throw cocotb exception
    else:
        # cocotbext-uart returns byteArray. Convert to bytes first, then to Binary value for uniformity.
        message_bytes = bytes(await uart_sink.read(count=6))
        message = cocotb.binary.BinaryValue(value=message_bytes, n_bits=48, bigEndian=False)
        print("After a wait of " + str(x) + "000 clocks, received message: ", end='')
        print("0x{0:0{width}x}".format(message.integer, width=12))
        return message


