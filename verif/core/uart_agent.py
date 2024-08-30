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
from cocotb.log import SimLog


CRC8_START = 0x0D
CRC_POLY = 0xC6


class UartCmd(Enum):
    READ = 0x0
    WRITE = 0x1

class UartResp(Enum):
    NACK = 0x0
    ACK_READ = 0x1
    ACK_WRITE = 0x2
    EVENT = 0x3

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
    baud_rate: int = 1000000
    command_pos: int = 43
    reserved_pos: int = 40
    addr_pos: int = 32
    data_pos: int = 0
    frame_size: int = 8
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
        self._dut_clk: Optional[ModifiableObject] = None
        self._log = SimLog("cocotb.%s" % (type(self).__qualname__))

    @property
    def uart_config(self) -> UartConfig:
        if self._uart_config is None:
            raise ValueError("property uart_config is not initialized")
        return self._uart_config

    @uart_config.setter
    def uart_config(self, uart_config) -> None:
        if not isinstance(uart_config, UartConfig):
            raise ValueError("property uart_config must be of type UartConfig")
        self._uart_config = uart_config

    @property
    def uart_source(self) -> UartSource:
        if self._uart_source is None:
            raise ValueError("property uart_source is not initialized")
        return self._uart_source

    @uart_source.setter
    def uart_source(self, uart_source) -> None:
        if not isinstance(uart_source, UartSource):
            raise ValueError("property uart_source must be of type UartSource")
        self._uart_source = uart_source

    @property
    def uart_sink(self) -> UartSink:
        if self._uart_sink is None:
            raise ValueError("property uart_sink is not initialized")
        return self._uart_sink

    @uart_sink.setter
    def uart_sink(self, uart_sink) -> None:
        if not isinstance(uart_sink, UartSink):
            raise ValueError("property uart_sink must be of type UartSink")
        self._uart_sink = uart_sink

    @property
    def dut_clk(self) -> ModifiableObject:
        if self._dut_clk is None:
            raise ValueError("property dut_clk is not initialized")
        return self._dut_clk

    @dut_clk.setter
    def dut_clk(self, dut_clk) -> None:
        if not isinstance(dut_clk, ModifiableObject):
            raise ValueError("property dut_clk must be of type ModifiableObject")
        self._dut_clk = dut_clk

    def _build_pkt(self, cmd: UartCmd, addr: RegAddr, data: int) -> BinaryValue:
        message = (
            (cmd.value << self.uart_config.command_pos)
            + (addr.value << self.uart_config.addr_pos)
            + (data << self.uart_config.data_pos)
        )
        return BinaryValue(
            value=message,
            n_bits=self.uart_config.packet_size,
            bigEndian=self.uart_config.endianness,
        )

    def _calc_crc8(self, bytes: bytes) -> int:
        current_crc = CRC8_START
        for byte in bytes:
            crc = int2ba(current_crc, 8)
            data_bits = int2ba(byte, 8)
            poly = int2ba(CRC_POLY, 8)
            for j in range(7, -1, -1):
                if crc[7] != data_bits[j]:
                    crc = (crc >> 1) ^ poly
                else:
                    crc >>= 1
            current_crc = ba2int(crc)
        return current_crc

    def attach(self, in_sig: ModifiableObject, out_sig: ModifiableObject, dut_clk: ModifiableObject) -> None:
        self.uart_source = UartSource(
            data=in_sig,
            baud=self.uart_config.baud_rate,
            bits=self.uart_config.frame_size,
        )
        self.uart_sink = UartSink(
            data=out_sig,
            baud=self.uart_config.baud_rate,
            bits=self.uart_config.frame_size,
        )
        self.dut_clk = dut_clk

    async def transaction(self, cmd: UartCmd, addr: RegAddr, data: int = 0, timeout_clk_cycle: int = 840) -> None:
        response: Coroutine = await start(
            self.wait_for_response(timeout_clk_cycle)
        )

        cmd_pkt: BinaryValue = self._build_pkt(cmd=cmd, addr=addr, data=data)

        await self.uart_source.write(cmd_pkt.buff)
        await self.uart_source.wait()

        raw_crc = self._calc_crc8(cmd_pkt.buff)
        crc_pkt = BinaryValue(
            value=raw_crc, n_bits=8, bigEndian=self._uart_config.endianness
        )
        await self.uart_source.write(crc_pkt.buff)
        await response

    async def wait_for_response(self, timeout_clk_cycles: int):
        nb_bytes_expected = self.uart_config.packet_size / 8 + 1
        for cycle in range(0, timeout_clk_cycles):
            if self.uart_sink.count() >= nb_bytes_expected:  ## 6 octets du message + le CRC
                break
            await ClockCycles(self.dut_clk, int(timeout_clk_cycles / nb_bytes_expected), rising=True)

        if cycle == timeout_clk_cycles - 1:
            self._log.info("Timeout for wait reply")
            raise RuntimeError("Timeout for wait reply")

        else:
            pkt_bytes = bytes(await self.uart_sink.read(count=int(self.uart_config.packet_size / 8)))
            pkt = BinaryValue(value=pkt_bytes, n_bits=self.uart_config.packet_size, bigEndian=False)
            self._log.info(
                "After a wait of " + str(cycle) + "000 clocks, received message: "
            )
            #self._log.info(f"0x{pkt.buff.hex()}")

    async def start_acquisition(self, stop_condition: callable, data: int):
        # Send the EVENT command packet (cmd=0x03)
        en_acquisiton_cmd: BinaryValue = self._build_pkt(cmd=UartCmd.WRITE, addr=RegAddr.CHANNEL_EN_BITS, data=data)
        
        # Write the command packet to the UART source
        await self.uart_source.write(en_acquisiton_cmd.buff)
        await self.uart_source.wait()

        # Send CRC for the command packet
        raw_crc = self._calc_crc8(en_acquisiton_cmd.buff)
        crc_pkt = BinaryValue(value=raw_crc, n_bits=8, bigEndian=self._uart_config.endianness)
        await self.uart_source.write(crc_pkt.buff)

        # Accumulate packets until the stop condition is met
        packets = []
        while not stop_condition():
            # Wait for a response
            await self.wait_for_response(timeout_clk_cycles=100)
            
            # Read the packet from the UART sink
            pkt = await self.uart_sink.read(count=int(self.uart_config.packet_size / 8))
            packets.append(pkt)
            
        return packets
