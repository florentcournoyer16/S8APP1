from dataclasses import dataclass
from enum import Enum
from cocotbext.uart import UartSource, UartSink
from cocotb.handle import ModifiableObject, HierarchyObject
from typing import Tuple, Optional
from cocotb.clock import Clock
from cocotb import start
from cocotb import Coroutine
from cocotb.binary import BinaryValue
from bitarray.util import int2ba, ba2int
from cocotb.triggers import ClockCycles
from logger import logger


CRC8_START = 0x0D
CRC_POLY = 0xC6


class Command(Enum):
    READ = 0x0
    WRITE = 0x1


class RegAddr(Enum):
    DATA_MODE = 0x00  # RW
    BIAS_MODE = 0x01  # RW
    EN_COUNT_RATE = 0x02  # RW
    EN_EVENT_COUNT_RATE = 0x03  # RW
    TDC_THRESH = 0x04  # RW
    SRC_SEL = 0x05  # RW
    SYNC_FLAG_ERR = 0x06  # R
    CLEAR_SYNC_FLAG = 0x07  # W
    CHANNEL_EN_BITS = 0x08  # RW
    PRODUCT_VER_ID = 0x09  # R


@dataclass
class UartConfig:
    baud_rate: int = 9600
    command_pos: int = 43
    reserved_pos: int = 40
    addr_pos: int = 32
    data_pos: int = 0
    packet_size: int = 48
    endianness: bool = False


class UartAgent:
    def __init__(
        self,
        uart_config: UartConfig,
    ):
        self.uart_config = uart_config
        self._uart_source: Optional[UartSource] = None
        self._uart_sink: Optional[UartSink] = None
        self._dut_clk: Optional[Clock] = None

    @property
    def uart_config(self) -> UartConfig:
        if self._uart_config is None:
            raise ValueError("property uart_config is not initialized")
        return self._uart_config

    @uart_config.setter
    def uart_config(self, uart_config):
        if not isinstance(uart_config, UartConfig):
            raise ValueError("property uart_config must be of type UartConfig")
        self._uart_config = uart_config

    @property
    def uart_source(self) -> UartConfig:
        if self._uart_source is None:
            raise ValueError("property uart_source is not initialized")
        return self._uart_source

    @uart_source.setter
    def uart_source(self, uart_source):
        if not isinstance(uart_source, UartSource):
            raise ValueError("property uart_source must be of type UartSource")
        self._uart_source = uart_source

    @property
    def uart_sink(self) -> UartSink:
        if self._uart_sink is None:
            raise ValueError("property uart_sink is not initialized")
        return self._uart_sink

    @uart_sink.setter
    def uart_sink(self, uart_sink):
        if not isinstance(uart_sink, UartSink):
            raise ValueError("property uart_sink must be of type UartSink")
        self._uart_sink = uart_sink

    @property
    def dut_clk(self) -> Clock:
        if self._dut_clk is None:
            raise ValueError("property dut_clk is not initialized")
        return self._dut_clk

    @dut_clk.setter
    def dut_clk(self, dut_clk):
        if not isinstance(dut_clk, UartSink):
            raise ValueError("property dut_clk must be of type Clock")
        self._dut_clk = dut_clk

    def attach(self, in_sig: ModifiableObject, out_sig: ModifiableObject, clk: Clock):
        self.uart_source = UartSource(
            data=in_sig,
            baud=self.uart_config.baud_rate,
            bits=self.uart_config.packet_size,
        )
        self.uart_sink = UartSink(
            data=out_sig,
            baud=self.uart_config.baud_rate,
            bits=self.uart_config.packet_size,
        )
        self._dut_clk = clk

    def build_cmd_msg(self, command: Command, addr: RegAddr, data: int):
        message = (
            (command << self.uart_config.command_pos)
            + (addr << self.uart_config.addr_pos)
            + (data << self.uart_config.data_pos)
        )
        return BinaryValue(
            value=message,
            n_bits=self.uart_config.packet_size,
            bigEndian=self.uart_config.endianess,
        )

    def print_cmd_msg(self, cmd_msg: BinaryValue):
        print("print Cocotb binary string : " + cmd_msg.binstr)
        print("print Cocotb integer       : " + "{}".format(cmd_msg.integer))
        print(
            "print Cocotb integer in hex: "
            + "0x{0:{width}x}".format(cmd_msg.integer, width=8)
        )
        print("print Cocotb byte buffer ", end="")
        print(cmd_msg.buff)
        print("print Cocotb byte byte per byte, seen as a serie of int   : ")
        for item in cmd_msg.buff:
            print("\t0x{0:2x} ".format(item), end="")  # hexadecimal
            print(item)  # decimal
        print()

    def calculate_crc8_single_cycle(self, data: int, current_crc: int):
        crc = int2ba(current_crc, 8)
        data_bits = int2ba(data, 8)
        poly = int2ba(CRC_POLY, 8)
        for j in range(7, -1, -1):
            if crc[7] != data_bits[j]:
                crc = (crc >> 1) ^ poly
            else:
                crc >>= 1
        return ba2int(crc)

    def calculate_crc8(self, value_array: bytes):
        current_crc = CRC8_START
        for b in value_array:
            current_crc = self.calculate_crc8_single_cycle(b, current_crc)
        return current_crc

    async def write(self, addr: RegAddr, data: int, timeout_ms: int = 1000):
        response: Coroutine = await start(
            self.wait_for_response(self.dut_clk, self.uart_sink, timeout_ms)
        )

        cmd_msg: BinaryValue = self.build_cmd_msg(
            command=Command.WRITE, addr=addr, data=data
        )

        # self.print_cmd_msg(cmd_msg)

        await self.uart_source.write(cmd_msg.buff)
        await self.uart_source.wait()

        raw_crc = self.calculate_crc8(cmd_msg.buff)
        crc_msg = BinaryValue(
            value=raw_crc, n_bits=8, bigEndian=self._uart_config.endianness
        )
        await self.uart_source.write(crc_msg.buff)
        await response

    async def read(self, addr: RegAddr, data: int = 0, timeout_ms: int = 1000):
        response: Coroutine = await start(
            self.wait_for_response(self.dut_clk, self.uart_sink, timeout_ms)
        )

        cmd_msg: BinaryValue = self.build_cmd_msg(
            command=Command.WRITE, addr=addr, data=data
        )

        # self.print_cmd_msg(cmd_msg)

        await self.uart_source.write(cmd_msg.buff)
        await self.uart_source.wait()

        raw_crc = self.calculate_crc8(cmd_msg.buff)
        crc_msg = BinaryValue(
            value=raw_crc, n_bits=8, bigEndian=self._uart_config.endianness
        )
        await self.uart_source.write(crc_msg.buff)
        await response

    async def wait_for_response(self, clk: Clock, uart_sink: UartSink, timeout_ms: int):
        nb_cycle = int((timeout_ms * 10**-3) / (clk.period * 10**-9))
        nb_bytes_expected = self.uart_config.packet_size / 8 + 1
        for x in range(0, nb_cycle):
            if uart_sink.count() >= nb_bytes_expected:  ## 6 octets du message + le CRC
                break
            await ClockCycles(clk, int(nb_cycle / nb_bytes_expected), rising=True)

        if x == nb_cycle:
            logger.info("Timeout for wait reply")
            raise RuntimeError("Timeout for wait reply")
            # or use plain assert.
            # assert False, "Timeout for wait reply"

        else:
            # cocotbext-uart returns byteArray. Convert to bytes first, then to Binary value for uniformity.
            message_bytes = bytes(await uart_sink.read(count=6))
            message = BinaryValue(value=message_bytes, n_bits=48, bigEndian=False)
            logger.info(
                "After a wait of " + str(x) + "000 clocks, received message: ", end=""
            )
            logger.info("0x{0:0{width}x}".format(message.integer, width=12))
