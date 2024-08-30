from dataclasses import dataclass, field
from enum import Enum
from cocotbext.uart import UartSource, UartSink
from cocotb.handle import ModifiableObject
from typing import Optional
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
    command_pos: tuple[int, int] = field(default_factory=lambda: (43, 48))
    reserved_pos: tuple[int, int] = field(default_factory=lambda: (40, 43))
    addr_pos: tuple[int, int] = field(default_factory=lambda: (32, 40))
    data_pos: tuple[int, int] = field(default_factory=lambda: (0, 32))
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
    def uart_config(self, uart_config: UartConfig) -> None:
        if not isinstance(uart_config, UartConfig):
            raise ValueError("property uart_config must be of type UartConfig")
        self._uart_config = uart_config

    @property
    def uart_source(self) -> UartSource:
        if self._uart_source is None:
            raise ValueError("property uart_source is not initialized")
        return self._uart_source

    @uart_source.setter
    def uart_source(self, uart_source: UartSource) -> None:
        if not isinstance(uart_source, UartSource):
            raise ValueError("property uart_source must be of type UartSource")
        self._uart_source = uart_source

    @property
    def uart_sink(self) -> UartSink:
        if self._uart_sink is None:
            raise ValueError("property uart_sink is not initialized")
        return self._uart_sink

    @uart_sink.setter
    def uart_sink(self, uart_sink: UartSink) -> None:
        if not isinstance(uart_sink, UartSink):
            raise ValueError("property uart_sink must be of type UartSink")
        self._uart_sink = uart_sink

    @property
    def dut_clk(self) -> ModifiableObject:
        if self._dut_clk is None:
            raise ValueError("property dut_clk is not initialized")
        return self._dut_clk

    @dut_clk.setter
    def dut_clk(self, dut_clk: ModifiableObject) -> None:
        if not isinstance(dut_clk, ModifiableObject):
            raise ValueError("property dut_clk must be of type ModifiableObject")
        self._dut_clk = dut_clk

    def _build_pkt(self, cmd: UartCmd, addr: RegAddr, data: int) -> BinaryValue:
        message = (
            (cmd.value << self.uart_config.command_pos[0])
            + (addr.value << self.uart_config.addr_pos[0])
            + (data << self.uart_config.data_pos[0])
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

    def _log_resp_packet(self, pkt: BinaryValue) -> None:
        pkt_str = pkt.binstr[::-1]

        command_start, command_end = self.uart_config.command_pos
        uart_resp_str: str = hex(int(pkt_str[command_start:command_end][::-1], 2))
        uart_resp: UartResp = UartResp(int(uart_resp_str, 16))

        addr_start, addr_end = self.uart_config.addr_pos
        uart_addr: str = hex(int(pkt_str[addr_start:addr_end][::-1], 2))

        data_start, data_end = self.uart_config.data_pos
        self._log.info(pkt_str[data_start:data_end])
        uart_data: str = hex(int(pkt_str[data_start:data_end][::-1], 2))

        self._log.info(f"UartResp: {uart_resp_str} ({uart_resp})")
        self._log.info(f"AddrReg: {uart_addr}")
        self._log.info(f"Data: {uart_data}")

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

    async def transaction(self, cmd: UartCmd, addr: RegAddr, data: int = 0, timeout_cycles: int = 1000, retries: int = 100) -> None:
        response: Coroutine = await start(self.wait_for_response(timeout_cycles, retries))

        cmd_pkt: BinaryValue = self._build_pkt(cmd=cmd, addr=addr, data=data)

        await self.uart_source.write(cmd_pkt.buff)
        await self.uart_source.wait()

        raw_crc8 = self._calc_crc8(cmd_pkt.buff)
        crc8_pkt = BinaryValue(
            value=raw_crc8,
            n_bits=self._uart_config.frame_size,
            bigEndian=self._uart_config.endianness
        )
        await self.uart_source.write(crc8_pkt.buff)
        await response

        self.uart_source.clear()
        self.uart_sink.clear()

    async def wait_for_response(self, timeout_cycles: int, retries: int):
        nb_bytes_expected = int(self.uart_config.packet_size / self._uart_config.frame_size + 1)
        try_counter = 1
        while (try_counter <= retries) and (self.uart_sink.count() < nb_bytes_expected):
            await ClockCycles(self.dut_clk, timeout_cycles, rising=True)
            try_counter += 1

        if try_counter == retries:
            self._log.error(f"Timeout after a wait of {str(timeout_cycles * retries)} clock cycles")
            raise RuntimeError(f"Timeout after a wait of {str(timeout_cycles * retries)} clock cycles")

        pkt_bytes = bytes(await self.uart_sink.read(count=int(self.uart_config.packet_size / self._uart_config.frame_size)))
        pkt = BinaryValue(value=pkt_bytes, n_bits=self.uart_config.packet_size, bigEndian=False)
        self._log.info(f"After a wait of {str(timeout_cycles * try_counter)} clock cycles, received message:")
        self._log_resp_packet(pkt)
        return pkt

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
            await self.wait_for_response(retries=100, timeout_cycles=100)
            
            # Read the packet from the UART sink
            pkt = await self.uart_sink.read(count=int(self.uart_config.packet_size / 8))
            packets.append(pkt)
            
        return packets
