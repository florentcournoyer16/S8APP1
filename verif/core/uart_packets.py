from dataclasses import dataclass, field
from typing import Tuple
from cocotb.binary import BinaryValue
from cocotb.log import SimLog
from enum import Enum
from logging import Logger
from base_model import RegAddr


class UartTxCmd(Enum):
    READ = 0x0
    WRITE = 0x1

class UartRxType(Enum):
    NACK = 0x0
    ACK_READ = 0x1
    ACK_WRITE = 0x2
    EVENT = 0x3

@dataclass
class UartTxPktStruct:
    cmd_pos: Tuple[int, int] = field(default_factory=lambda: (43, 48))
    res_pos: Tuple[int, int] = field(default_factory=lambda: (40, 43))
    addr_pos: Tuple[int, int] = field(default_factory=lambda: (32, 40))
    data_pos: Tuple[int, int] = field(default_factory=lambda: (0, 32))
    
@dataclass
class UartRxPktStruct:
    type_pos: Tuple[int, int] = field(default_factory=lambda: (43, 48))
    res1_pos: Tuple[int, int] = field(default_factory=lambda: (40, 43))
    num_pos: Tuple[int, int] = field(default_factory=lambda: (38, 40))
    chan_pos: Tuple[int, int] = field(default_factory=lambda: (34, 38))
    res0_pos: Tuple[int, int] = field(default_factory=lambda: (32, 34))
    data_pos: Tuple[int, int] = field(default_factory=lambda: (0, 32))

@dataclass
class UartConfig:
    baud_rate: int = 1000000
    frame_size: int = 8
    packet_size: int = 48
    big_endian: bool = False
    tx_pkt_struct: UartTxPktStruct = UartTxPktStruct()
    rx_pkt_struct: UartRxPktStruct = UartRxPktStruct()

class UartTxPckt(BinaryValue):
    def __init__(self, cmd: UartTxCmd, addr: RegAddr, data: int, uart_config: UartConfig):
        self.cmd: UartTxCmd = cmd
        self.addr: RegAddr = addr
        self.data: int = data
        self.uart_config: UartConfig = uart_config
        self.message: int = (
            (cmd.value << self.uart_config.tx_pkt_struct.cmd_pos[0])
            + (addr.value << self.uart_config.tx_pkt_struct.addr_pos[0])
            + (data << self.uart_config.tx_pkt_struct.data_pos[0])
        )
        super(UartTxPckt, self).__init__(
            value=self.message,
            n_bits=self.uart_config.packet_size,
            bigEndian=self.uart_config.big_endian,
        )
        self._log: Logger = SimLog("cocotb.%s" % (type(self).__qualname__))

    def log_pkt(self) -> None:
        self._log.info("\tCMD: %s", self.cmd)
        self._log.info("\tRES: %s", "0x0")
        self._log.info("\tADDR: %s", self.addr)
        self._log.info("\tDATA: %s", hex(self.data))



class UartRxPckt(BinaryValue):
    def __init__(self, rx_pkt_bytes: bytes, uart_config: UartConfig):
        self.uart_config: UartConfig = uart_config
        super().__init__(
            value=rx_pkt_bytes,
            n_bits=self.uart_config.packet_size,
            bigEndian=self.uart_config.big_endian
        )
        pkt_str = self.binstr[::-1]
        

        type_start, type_end = self.uart_config.rx_pkt_struct.type_pos
        res1_start, res1_end = self.uart_config.rx_pkt_struct.res1_pos
        num_start, num_end = self.uart_config.rx_pkt_struct.num_pos
        chan_start, chan_end = self.uart_config.rx_pkt_struct.chan_pos
        res0_start, res0_end = self.uart_config.rx_pkt_struct.res0_pos
        data_start, data_end = self.uart_config.rx_pkt_struct.data_pos

        self.type: UartRxType = UartRxType(int(pkt_str[type_start:type_end][::-1], 2))
        self.res1: str = hex(int(pkt_str[res1_start:res1_end][::-1], 2))
        self.num: str = hex(int(pkt_str[num_start:num_end][::-1], 2))
        self.chan: str = hex(int(pkt_str[chan_start:chan_end][::-1], 2))
        self.res0: str = hex(int(pkt_str[res0_start:res0_end][::-1], 2))
        self.data: str = hex(int(pkt_str[data_start:data_end][::-1], 2))
        self._log: Logger = SimLog("cocotb.%s" % (type(self).__qualname__))

    def log_pkt(self):
        self._log.info("\tTYPE: %s", self.type)
        self._log.info("\tRES1: %s", self.res1)
        self._log.info("\tNUM: %s", self.num)
        self._log.info("\tCHAN: %s", self.chan)
        self._log.info("\tRES0: %s", self.res0)
        self._log.info("\tDATA: %s", self.data)
